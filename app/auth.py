"""
auth.py — Módulo de autenticación y autorización por roles.
Contiene: usuarios mock, permisos por rol, decoradores de acceso
y la estructura del menú lateral filtrada por permisos.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort
import config
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException

# ──────────────────────────────────────────────
# Usuarios mock (en producción → LDAP / AD)
# ──────────────────────────────────────────────
USERS = {
    'admin': {
        'password': 'admin123',
        'nombre': 'Jorge López',
        'rol': 'admin',
        'email': 'jlopez@itu.edu.ar',
    },
    'tecnico': {
        'password': 'tecnico123',
        'nombre': 'Carlos Ruiz',
        'rol': 'tecnico',
        'email': 'cruiz@itu.edu.ar',
    },
    'docente': {
        'password': 'docente123',
        'nombre': 'Ana Torres',
        'rol': 'docente',
        'email': 'atorres@itu.edu.ar',
    },
    'alumno': {
        'password': 'alumno123',
        'nombre': 'María Gómez',
        'rol': 'alumno',
        'email': 'mgomez@itu.edu.ar',
    },
}

# ──────────────────────────────────────────────
# Permisos por rol
# Cada clave es un "permiso" que se mapea a
# una o varias rutas/funcionalidades.
# ──────────────────────────────────────────────
ROLE_PERMISSIONS = {
    'admin': [
        'dashboard',
        'equipos', 'equipo_detalle', 'equipo_nuevo', 'equipo_editar', 'equipo_eliminar',
        'componentes',
        'mantenimiento',
        'asignaciones',
    ],
    'tecnico': [
        'dashboard',
        'equipos', 'equipo_detalle',
        'componentes',
        'mantenimiento',
        'asignaciones',
    ],
    'docente': [
        'dashboard',
        'equipos', 'equipo_detalle',
        'asignaciones',
    ],
    'alumno': [
        'dashboard',
        'equipo_detalle',
        'asignaciones',
    ],
}

# ──────────────────────────────────────────────
# Etiquetas legibles para cada rol
# ──────────────────────────────────────────────
ROLE_LABELS = {
    'admin': 'Administrador',
    'tecnico': 'Técnico',
    'docente': 'Docente',
    'alumno': 'Alumno',
}

# ──────────────────────────────────────────────
# Estructura del menú lateral (sidebar)
# Cada sección tiene un título y una lista de
# ítems con: label, icon, href y permiso req.
# ──────────────────────────────────────────────
SIDEBAR_MENU = [
    {
        'section': None,  # Sin encabezado de sección
        'items': [
            {'label': 'Dashboard', 'icon': 'fa-solid fa-border-all', 'href': 'equipos', 'permission': 'dashboard', 'active_id': 'dashboard'},
        ]
    },
    {
        'section': 'Inventario y Soporte',
        'items': [
            {'label': 'Componentes (MongoDB)', 'icon': 'fa-solid fa-microchip', 'href': 'componentes', 'permission': 'componentes', 'active_id': 'componentes'},
            {'label': 'Mantenimiento',         'icon': 'fa-solid fa-wrench',    'href': 'mantenimiento', 'permission': 'mantenimiento', 'active_id': 'mantenimiento'},
        ]
    },
    {
        'section': 'Ubicación y Asignación',
        'items': [
            {'label': 'Asignaciones',          'icon': 'fa-solid fa-users-viewfinder', 'href': 'asignaciones', 'permission': 'asignaciones',  'active_id': 'asignaciones'},
        ]
    },
]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _authenticate_ldap(username, password):
    """Valida credenciales contra el Active Directory institucional."""
    try:
        # 1. Conexión y Bind con cuenta de servicio
        server = Server(config.LDAP_HOST, port=config.LDAP_PORT, use_ssl=config.LDAP_USE_SSL, get_info=ALL)
        conn = Connection(server, user=config.LDAP_BIND_USER, password=config.LDAP_BIND_PASSWORD, auto_bind=True, receive_timeout=config.LDAP_TIMEOUT)
        
        # 2. Buscar al usuario
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        conn.search(config.AD_BASE_DN, search_filter, search_scope=SUBTREE, attributes=['cn', 'mail', 'memberOf', 'distinguishedName'])
        
        if not conn.entries:
            conn.unbind()
            return None # Usuario no encontrado
            
        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn
        
        # 3. Intentar Bind con las credenciales del usuario para verificar contraseña
        user_conn = Connection(server, user=user_dn, password=password)
        if not user_conn.bind():
            conn.unbind()
            return None # Contraseña incorrecta
        user_conn.unbind()
        
        # 4. Obtener grupos y mapear a rol
        rol_asignado = config.AD_DEFAULT_ROLE
        member_of = user_entry.memberOf.values if 'memberOf' in user_entry else []
        
        # Extraer el CN de cada grupo (ej: CN=Administradores,OU=... -> Administradores)
        user_groups = []
        for group_dn in member_of:
            parts = group_dn.split(',')
            if parts and parts[0].startswith('CN='):
                user_groups.append(parts[0][3:])
                
        # Buscar el primer grupo que haga match con nuestro mapa
        for group in user_groups:
            if group in config.AD_GROUP_ROLE_MAP:
                rol_asignado = config.AD_GROUP_ROLE_MAP[group]
                break
                
        # 5. Construir objeto usuario
        nombre = str(user_entry.cn) if 'cn' in user_entry else username
        email = str(user_entry.mail) if 'mail' in user_entry else f"{username}@{config.AD_DOMAIN}"
        
        conn.unbind()
        
        return {
            'username': username,
            'nombre': nombre,
            'rol': rol_asignado,
            'email': email
        }
        
    except LDAPException as e:
        print(f"[LDAP ERROR] {e}")
        return None

def _authenticate_local(username, password):
    """Valida credenciales contra el diccionario local (Fallback)."""
    user = USERS.get(username)
    if user and user['password'] == password:
        u = user.copy()
        u['username'] = username
        return u
    return None

def authenticate(username, password):
    """Punto de entrada unificado para autenticación."""
    if config.AUTH_MODE == 'ldap':
        return _authenticate_ldap(username, password)
    else:
        return _authenticate_local(username, password)

def get_current_user():
    """Devuelve la info del usuario logueado desde la sesión, o None."""
    user = session.get('user')
    if user:
        # Asegurarse de tener el label para la UI
        user['label'] = ROLE_LABELS.get(user['rol'], user['rol'])
        return user
    return None


def has_permission(permission):
    """Verifica si el usuario actual tiene un permiso dado."""
    user = get_current_user()
    if not user:
        return False
    return permission in ROLE_PERMISSIONS.get(user['rol'], [])


def get_filtered_menu():
    """Devuelve la estructura del sidebar filtrada
    según los permisos del usuario actual."""
    user = get_current_user()
    if not user:
        return []

    user_perms = ROLE_PERMISSIONS.get(user['rol'], [])
    filtered = []

    for section in SIDEBAR_MENU:
        visible_items = [
            item for item in section['items']
            if item['permission'] in user_perms
        ]
        if visible_items:
            filtered.append({
                'section': section['section'],
                'items': visible_items,
            })

    return filtered


# ──────────────────────────────────────────────
# Decoradores
# ──────────────────────────────────────────────
def login_required(f):
    """Redirige a /login si no hay sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(permission):
    """Restringe el acceso a una vista según el permiso.
    Uso: @role_required('equipos')"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash('Debe iniciar sesión para acceder.', 'warning')
                return redirect(url_for('login'))
            if permission not in ROLE_PERMISSIONS.get(user['rol'], []):
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ──────────────────────────────────────────────
# Context Processor (inyecta datos en templates)
# ──────────────────────────────────────────────
def inject_auth_context():
    """Retorna un dict que Jinja2 recibirá en TODAS las plantillas.
    Se registra en app.py con @app.context_processor."""
    user = get_current_user()
    return {
        'current_user': user,
        'sidebar_menu': get_filtered_menu(),
        'has_permission': has_permission,
    }
