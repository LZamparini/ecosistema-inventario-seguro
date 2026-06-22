"""
config.py — Configuración centralizada del proyecto.
Usa variables de entorno con valores por defecto para desarrollo.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ──────────────────────────────────────────────
# Modo de autenticación
# 'ldap'  → Valida contra Active Directory real
# 'local' → Usa usuarios mock (desarrollo sin red)
# ──────────────────────────────────────────────
AUTH_MODE = os.environ.get('AUTH_MODE', 'local')

# ──────────────────────────────────────────────
# Configuración LDAP / Active Directory
# ──────────────────────────────────────────────
LDAP_HOST = os.environ.get('LDAP_HOST', '127.0.0.1')
LDAP_PORT = int(os.environ.get('LDAP_PORT', 389))
LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'false').lower() == 'true'

# Dominio AD
AD_DOMAIN = os.environ.get('AD_DOMAIN', 'dominio.local')
AD_BASE_DN = os.environ.get('AD_BASE_DN', 'DC=dominio,DC=local')

# Cuenta de servicio para hacer búsquedas LDAP
# (bind inicial antes de validar las credenciales del usuario)
LDAP_BIND_USER = os.environ.get('LDAP_BIND_USER', '')
LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', '')

# Mapeo: Nombre del grupo de AD → Rol en la aplicación
# Ajustar los nombres de grupo según lo configurado en el AD real
AD_GROUP_ROLE_MAP = {
    'G_Administradores': 'admin',
    'G_Tecnicos':        'tecnico',
    'G_Docentes':        'docente',
    'G_Alumnos':         'alumno',
    # Grupos por defecto de Windows (fallback)
    'Domain Admins':    'admin',
    'Admins':           'admin',
}

# Rol por defecto si el usuario no pertenece a ningún grupo mapeado
AD_DEFAULT_ROLE = os.environ.get('AD_DEFAULT_ROLE', 'alumno')

# Timeout para conexiones LDAP (segundos)
LDAP_TIMEOUT = int(os.environ.get('LDAP_TIMEOUT', 10))

# ──────────────────────────────────────────────
# Configuración SQL Server
# ──────────────────────────────────────────────
SQL_SERVER_HOST = os.environ.get('SQL_SERVER_HOST', '127.0.0.1')
SQL_SERVER_PORT = int(os.environ.get('SQL_SERVER_PORT', 1433))
SQL_SERVER_USER = os.environ.get('SQL_SERVER_USER', 'sa')
SQL_SERVER_PASSWORD = os.environ.get('SQL_SERVER_PASSWORD', '')
SQL_SERVER_DATABASE = os.environ.get('SQL_SERVER_DATABASE', 'ubicacion_db')

# ──────────────────────────────────────────────
# Configuración MongoDB
# ──────────────────────────────────────────────
MONGO_HOST = os.environ.get('MONGO_HOST', '127.0.0.1')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'inventario')
MONGO_USER = os.environ.get('MONGO_USER', 'root')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')

# ──────────────────────────────────────────────
# Flask
# ──────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-cambiar-en-produccion')

