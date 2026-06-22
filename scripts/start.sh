#!/bin/bash

echo "================================================"
echo "  EGI - Ecosistema de Inventario Seguro"
echo "  Script de arranque completo"
echo "================================================"

NAMESPACE="inventario-seguro"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ─── 1. Levantar Minikube ────────────────────────────────────────────────────
echo ""
echo "[1/7] Levantando Minikube..."
minikube start
if [ $? -ne 0 ]; then
  echo "ERROR: No se pudo levantar Minikube. Abortando."
  exit 1
fi
echo "Minikube listo."

# ─── Limpiar deployments anteriores ─────────────────────────────────────────
echo ""
echo "[0/7] Limpiando despliegues anteriores..."
kubectl delete deployments --all -n inventario-seguro > /dev/null 2>&1
kubectl delete jobs --all -n inventario-seguro > /dev/null 2>&1
sleep 3
echo "Limpieza lista."

# ─── 2. Namespace ────────────────────────────────────────────────────────────
echo ""
echo "[2/7] Verificando namespace $NAMESPACE..."
kubectl get namespace $NAMESPACE > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creando namespace $NAMESPACE..."
  kubectl create namespace $NAMESPACE
fi
echo "Namespace listo."

# ─── 3. Secrets y ConfigMap ──────────────────────────────────────────────────
echo ""
echo "[3/7] Aplicando Secrets y ConfigMap..."
kubectl apply -f "$REPO_DIR/k8s/frontend/secret.yaml"
kubectl apply -f "$REPO_DIR/k8s/frontend/configmap.yaml"
echo "Secrets y ConfigMap aplicados."

# ─── 4. MongoDB ──────────────────────────────────────────────────────────────
echo ""
echo "[4/7] Desplegando MongoDB..."
kubectl apply -f "$REPO_DIR/k8s/mongo-db/"
echo "Esperando que MongoDB esté listo..."
kubectl wait --for=condition=Ready pod -l app=inventario-db -n $NAMESPACE --timeout=120s
if [ $? -eq 0 ]; then
  echo "MongoDB listo."
  echo "Ejecutando seed de MongoDB..."
  kubectl delete job mongo-seed -n $NAMESPACE > /dev/null 2>&1
  kubectl apply -f "$REPO_DIR/k8s/mongo-db/seed-job.yaml"
  echo "Seed iniciado (corre en segundo plano)."
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
kubectl apply -f "$REPO_DIR/k8s/frontend/deployment.yaml"
echo "Esperando que Flask esté listo..."
sleep 5
OLD_POD=$(kubectl get pods -n $NAMESPACE -l app=inventario-web \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$OLD_POD" ]; then
  kubectl delete pod $OLD_POD -n $NAMESPACE > /dev/null 2>&1
fi
kubectl wait --for=condition=Ready pod -l app=inventario-web -n $NAMESPACE --timeout=120s
if [ $? -eq 0 ]; then
  echo "Flask listo."
else
  echo "ADVERTENCIA: Flask tardó más de lo esperado. Verificá los logs con:"
  echo "  kubectl logs -n $NAMESPACE deploy/inventario-web"
fi

# ─── 7. Exponer la app en la red ─────────────────────────────────────────────
echo ""
echo "[7/7] Exponiendo la app en la red local..."
MY_IP=$(ip addr show enp0s8 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$MY_IP" ]; then
  MY_IP=$(hostname -I | awk '{print $1}')
fi

echo ""
echo "================================================"
echo "  TODO LISTO"
echo ""
echo "  Pods corriendo:"
kubectl get pods -n $NAMESPACE
echo ""
echo "  Abrí en cualquier PC de la red:"
echo "  http://$MY_IP:8080"
echo ""
echo "  Usuario de prueba: tecnico.inventario"
echo "  Contraseña:        Itu2026*"
echo "================================================"
echo ""
echo "Iniciando reenvío de puertos... (Ctrl+C para detener)"
socat TCP-LISTEN:8080,bind=$MY_IP,fork TCP:192.168.49.2:30080
