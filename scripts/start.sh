#!/bin/bash

echo "================================================"
echo "  EGI - Ecosistema de Inventario Seguro"
echo "  Script de arranque completo y exposición"
echo "================================================"

NAMESPACE="inventario-seguro"
# Forzamos que la ruta base sea donde está el script realmente
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ─── 1. Levantar Minikube ────────────────────────────────────────────────────
echo ""
echo "[1/7] Levantando Minikube..."
minikube start
if [ $? -ne 0 ]; then
  echo "ERROR: No se pudo levantar Minikube. Abortando."
  exit 1
fi
echo "Minikube listo."

# ─── 2. Namespace ────────────────────────────────────────────────────────────
echo ""
echo "[2/7] Verificando namespace $NAMESPACE..."
kubectl get namespace $NAMESPACE > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creando namespace $NAMESPACE..."
  kubectl create namespace $NAMESPACE
fi
echo "Namespace listo."

# ─── 0. Limpiar despliegues anteriores (CORREGIDO) ───────────────────────────
echo ""
echo "[0/7] Limpiando despliegues anteriores y Pods residuales..."
# Quitamos el flag --quiet que rompía todo
kubectl delete deployments --all -n $NAMESPACE --ignore-not-found
kubectl delete jobs --all -n $NAMESPACE --ignore-not-found

echo "Destruyendo Pods residuales de forma forzada..."
kubectl delete pods --all -n $NAMESPACE --force --grace-period=0 > /dev/null 2>&1
sleep 3
echo "Limpieza profunda completada."

# ─── 3. Secrets y ConfigMap ──────────────────────────────────────────────────
echo ""
echo "[3/7] Aplicando Secrets y ConfigMap..."
kubectl apply -f "$REPO_DIR/k8s/frontend/secret.yaml" -n $NAMESPACE
kubectl apply -f "$REPO_DIR/k8s/frontend/configmap.yaml" -n $NAMESPACE
echo "Secrets y ConfigMap aplicados."

# ─── 4. MongoDB ──────────────────────────────────────────────────────────────
echo ""
echo "[4/7] Desplegando MongoDB..."
kubectl apply -f "$REPO_DIR/k8s/mongo-db/" -n $NAMESPACE
echo "Esperando que MongoDB esté listo..."
# Aseguramos el namespace en el wait
kubectl wait --for=condition=Ready pod -l app=inventario-db -n $NAMESPACE --timeout=120s
if [ $? -eq 0 ]; then
  echo "MongoDB listo."
  echo "Ejecutando seed de MongoDB..."
  kubectl delete job mongo-seed -n $NAMESPACE > /dev/null 2>&1
  kubectl apply -f "$REPO_DIR/k8s/mongo-db/seed-job.yaml" -n $NAMESPACE
  echo "Seed iniciado."
else
  echo "ADVERTENCIA: MongoDB tardó más de lo esperado. Continuando..."
fi

# ─── 5. Pedir IP de pfSense ──────────────────────────────────────────────────
echo ""
echo "[5/7] Configurando IP de pfSense..."
echo ">>> Mirá la pantalla de pfSense y fijate la IP de la interfaz WAN."
read -p ">>> Ingresá la IP de pfSense: " PFSENSE_IP
kubectl patch configmap pfsense-config -n $NAMESPACE \
  --type merge -p "{\"data\":{\"PFSENSE_WAN_IP\":\"$PFSENSE_IP\"}}"
echo "ConfigMap actualizado con IP $PFSENSE_IP."

# ─── 6. Flask App ────────────────────────────────────────────────────────────
echo ""
echo "[6/7] Desplegando aplicación Flask..."
kubectl apply -f "$REPO_DIR/k8s/frontend/deployment.yaml" -n $NAMESPACE
echo "Esperando que Flask esté listo..."

kubectl wait --for=condition=Ready pod -l app=inventario-web -n $NAMESPACE --timeout=120s
if [ $? -eq 0 ]; then
  echo "Flask listo."
else
  echo "ADVERTENCIA: Flask tardó más de lo esperado."
fi

# ─── 7. Exponer la app en la red ─────────────────────────────────────────────
echo ""
echo "[7/7] Exponiendo la app en la red local..."
MY_IP=$(ip addr show enp0s3 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$MY_IP" ]; then
  MY_IP=$(hostname -I | awk '{print $1}')
fi

echo ""
echo "========================================================"
echo "  TODO LISTO PARA LA DEFENSAS DE LA EGI"
echo ""
echo "  Pods corriendo actualmente:"
kubectl get pods -n $NAMESPACE
echo ""
echo "  Abrí en cualquier PC / Celular de la misma red:"
echo "  URL: http://$MY_IP:5000/componentes"
echo "========================================================"
echo ""
echo "Iniciando reenvío de puertos nativo... (Ctrl+C para detener)"

kubectl port-forward service/inventario-web 5000:5000 --address 0.0.0.0 -n $NAMESPACE
