"""
db.py — Módulo para conectar a SQL Server (pymssql) y MongoDB (pymongo).
"""

import pymssql
from pymongo import MongoClient
from bson import ObjectId
import config

# ──────────────────────────────────────────────
# SQL Server
# ──────────────────────────────────────────────

def get_db_connection():
    """Establece una conexión al motor SQL Server según config.py"""
    try:
        conn = pymssql.connect(
            server=config.SQL_SERVER_HOST,
            port=config.SQL_SERVER_PORT,
            user=config.SQL_SERVER_USER,
            password=config.SQL_SERVER_PASSWORD,
            database=config.SQL_SERVER_DATABASE,
            autocommit=True
        )
        return conn
    except Exception as e:
        print(f"[SQL ERROR] No se pudo conectar a la base de datos: {e}")
        return None

def test_db_connection():
    """Verifica si la base de datos responde. Usado para healthchecks."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS status")
                row = cursor.fetchone()
                return row is not None and row[0] == 1
        except Exception:
            return False
        finally:
            conn.close()
    return False


def get_equipo_sql_details(id_equipo):
    """Obtiene detalles de ubicación y responsable desde SQL Server para un id_equipo."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor(as_dict=True) as cursor:
            query = """
            SELECT 
                e.id_equipo,
                e.codigo_inventario,
                e.numero_banco,
                e.estado,
                e.fecha_ingreso,
                a.nombre AS aula_nombre,
                a.tipo AS aula_tipo,
                a.piso AS aula_piso,
                a.edificio AS aula_edificio,
                r.nombre AS responsable_nombre,
                r.apellido AS responsable_apellido,
                r.email AS responsable_email
            FROM equipos e
            LEFT JOIN aulas a ON e.id_aula = a.id_aula
            LEFT JOIN responsables r ON e.id_responsable = r.id_responsable
            WHERE e.id_equipo = %s
            """
            cursor.execute(query, (id_equipo,))
            return cursor.fetchone()
    except Exception as e:
        print(f"[SQL ERROR] Error fetching equipo SQL details for {id_equipo}: {e}")
        return None
    finally:
        conn.close()


def get_active_assignments(usuario_uid=None, rol=None):
    """Obtiene asignaciones activas desde SQL Server.
    Filtra por usuario_uid si el rol es docente o alumno."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(as_dict=True) as cursor:
            query = """
            SELECT 
                a.id_asignacion,
                a.id_equipo,
                a.usuario_uid,
                a.rol_assigned,
                a.fecha_desde,
                a.fecha_hasta,
                a.activa,
                e.codigo_inventario,
                au.nombre AS aula_nombre,
                e.numero_banco
            FROM asignaciones a
            JOIN equipos e ON a.id_equipo = e.id_equipo
            LEFT JOIN aulas au ON e.id_aula = au.id_aula
            WHERE a.activa = 1
            """
            params = []
            if usuario_uid and rol not in ['admin', 'tecnico']:
                query += " AND a.usuario_uid = %s"
                params.append(usuario_uid)
            
            query += " ORDER BY a.fecha_desde DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            for r in rows:
                if r['fecha_desde']:
                    r['fecha_desde_str'] = r['fecha_desde'].strftime('%d/%m/%Y')
                else:
                    r['fecha_desde_str'] = '-'
                if r['fecha_hasta']:
                    r['fecha_hasta_str'] = r['fecha_hasta'].strftime('%d/%m/%Y')
                else:
                    r['fecha_hasta_str'] = '-'
            return rows
    except Exception as e:
        print(f"[SQL ERROR] Error fetching active assignments: {e}")
        return []
    finally:
        conn.close()


# ──────────────────────────────────────────────
# MongoDB — Conexión
# ──────────────────────────────────────────────

_mongo_client = None

def get_mongo_client():
    """Retorna un MongoClient singleton (reutiliza la conexión)."""
    global _mongo_client
    if _mongo_client is None:
        try:
            if config.MONGO_PASSWORD:
                uri = (
                    f"mongodb://{config.MONGO_USER}:{config.MONGO_PASSWORD}"
                    f"@{config.MONGO_HOST}:{config.MONGO_PORT}/"
                    f"?authSource=admin"
                )
            else:
                uri = f"mongodb://{config.MONGO_HOST}:{config.MONGO_PORT}/"
            _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        except Exception as e:
            print(f"[MONGO ERROR] No se pudo crear el cliente MongoDB: {e}")
            return None
    return _mongo_client


def get_mongo_db():
    """Retorna la base de datos MongoDB configurada."""
    client = get_mongo_client()
    if client:
        return client[config.MONGO_DATABASE]
    return None


def test_mongo_connection():
    """Verifica si MongoDB responde. Usado para healthchecks."""
    try:
        client = get_mongo_client()
        if client:
            client.admin.command('ping')
            return True
    except Exception as e:
        print(f"[MONGO ERROR] Healthcheck falló: {e}")
    return False


# ──────────────────────────────────────────────
# MongoDB — CRUD para colección 'hardware'
# ──────────────────────────────────────────────

def get_all_hardware(filtro=None):
    """Retorna todos los documentos de la colección hardware.
    Opcionalmente aplica un filtro de búsqueda por texto."""
    db = get_mongo_db()
    if db is None:
        return []
    try:
        query = {}
        if filtro:
            # Búsqueda flexible: por id_equipo, fabricante, modelo o tipo
            query = {
                '$or': [
                    {'id_equipo': {'$regex': filtro, '$options': 'i'}},
                    {'fabricante': {'$regex': filtro, '$options': 'i'}},
                    {'modelo': {'$regex': filtro, '$options': 'i'}},
                    {'tipo': {'$regex': filtro, '$options': 'i'}},
                    {'cpu.modelo': {'$regex': filtro, '$options': 'i'}},
                    {'sistema_operativo.nombre': {'$regex': filtro, '$options': 'i'}},
                ]
            }
        return list(db.hardware.find(query).sort('id_equipo', 1))
    except Exception as e:
        print(f"[MONGO ERROR] Error al obtener hardware: {e}")
        return []


def get_hardware_by_id(id_equipo):
    """Busca un documento de hardware por su campo id_equipo."""
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return db.hardware.find_one({'id_equipo': id_equipo})
    except Exception as e:
        print(f"[MONGO ERROR] Error al buscar hardware '{id_equipo}': {e}")
        return None


def insert_hardware(data):
    """Inserta un nuevo documento de hardware. Retorna True si fue exitoso."""
    db = get_mongo_db()
    if db is None:
        return False
    try:
        # Verificar que no exista un equipo con el mismo id_equipo
        if db.hardware.find_one({'id_equipo': data.get('id_equipo')}):
            return False  # Ya existe
        db.hardware.insert_one(data)
        return True
    except Exception as e:
        print(f"[MONGO ERROR] Error al insertar hardware: {e}")
        return False


def update_hardware(id_equipo, data):
    """Actualiza un documento de hardware existente. Retorna True si fue exitoso."""
    db = get_mongo_db()
    if db is None:
        return False
    try:
        result = db.hardware.update_one(
            {'id_equipo': id_equipo},
            {'$set': data}
        )
        return result.modified_count > 0 or result.matched_count > 0
    except Exception as e:
        print(f"[MONGO ERROR] Error al actualizar hardware '{id_equipo}': {e}")
        return False


def delete_hardware(id_equipo):
    """Elimina un documento de hardware. Retorna True si fue exitoso."""
    db = get_mongo_db()
    if db is None:
        return False
    try:
        result = db.hardware.delete_one({'id_equipo': id_equipo})
        return result.deleted_count > 0
    except Exception as e:
        print(f"[MONGO ERROR] Error al eliminar hardware '{id_equipo}': {e}")
        return False


# ──────────────────────────────────────────────
# SQL Server — Nuevas operaciones
# ──────────────────────────────────────────────

def get_aulas():
    """Obtiene todas las aulas de SQL Server."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute("SELECT id_aula, nombre, tipo, piso, edificio FROM aulas ORDER BY nombre")
            return cursor.fetchall()
    except Exception as e:
        print(f"[SQL ERROR] Error fetching aulas: {e}")
        return []
    finally:
        conn.close()


def get_responsables():
    """Obtiene todos los responsables de SQL Server."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute("SELECT id_responsable, nombre, apellido, email FROM responsables ORDER BY nombre, apellido")
            return cursor.fetchall()
    except Exception as e:
        print(f"[SQL ERROR] Error fetching responsables: {e}")
        return []
    finally:
        conn.close()


def insert_equipo_sql(data):
    """Inserta un nuevo equipo en la base de datos SQL Server."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            query = """
            INSERT INTO equipos (id_equipo, codigo_inventario, id_aula, numero_banco, estado, id_responsable, fecha_ingreso)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['id_equipo'],
                data['codigo_inventario'],
                int(data['id_aula']),
                data['numero_banco'],
                data['estado'],
                int(data['id_responsable']) if data.get('id_responsable') else None,
                data['fecha_ingreso']
            ))
            return True
    except Exception as e:
        print(f"[SQL ERROR] Error inserting equipo: {e}")
        return False
    finally:
        conn.close()


def get_all_mantenimientos():
    """Obtiene todos los mantenimientos históricos y agendados de SQL Server."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(as_dict=True) as cursor:
            query = """
            SELECT 
                m.id_mant,
                m.id_equipo,
                m.fecha_mant,
                m.tipo,
                m.descripcion,
                m.tecnico,
                m.proximo_mant,
                a.nombre AS aula_nombre,
                e.numero_banco
            FROM mantenimientos m
            JOIN equipos e ON m.id_equipo = e.id_equipo
            LEFT JOIN aulas a ON e.id_aula = a.id_aula
            ORDER BY m.fecha_mant DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for r in rows:
                if r['fecha_mant']:
                    r['fecha_mant_str'] = r['fecha_mant'].strftime('%d/%m/%Y')
                else:
                    r['fecha_mant_str'] = '-'
                if r['proximo_mant']:
                    r['proximo_mant_str'] = r['proximo_mant'].strftime('%d/%m/%Y')
                else:
                    r['proximo_mant_str'] = '-'
            return rows
    except Exception as e:
        print(f"[SQL ERROR] Error fetching mantenimientos: {e}")
        return []
    finally:
        conn.close()


def insert_mantenimiento_sql(data):
    """Inserta un nuevo mantenimiento en SQL Server y pone al equipo en_reparacion."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            # 1. Insertar el registro de mantenimiento
            query_insert = """
            INSERT INTO mantenimientos (id_equipo, fecha_mant, tipo, descripcion, tecnico, proximo_mant)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_insert, (
                data['id_equipo'],
                data['fecha_mant'],
                data['tipo'],
                data['descripcion'],
                data['tecnico'],
                data.get('proximo_mant')
            ))
            
            # 2. Actualizar el estado del equipo a 'en_reparacion'
            query_update = """
            UPDATE equipos
            SET estado = 'en_reparacion'
            WHERE id_equipo = %s
            """
            cursor.execute(query_update, (data['id_equipo'],))
            return True
    except Exception as e:
        print(f"[SQL ERROR] Error registering mantenimiento: {e}")
        return False
    finally:
        conn.close()

# ──────────────────────────────────────────────
# Solicitudes (MongoDB) & Asignaciones (SQL Server)
# ──────────────────────────────────────────────

def insert_solicitud_mongo(data):
    db = get_mongo_db()
    if db is None:
        return False
    try:
        db.solicitudes.insert_one(data)
        return True
    except Exception as e:
        print(f"[MONGO ERROR] Error insertando solicitud: {e}")
        return False

def get_pending_solicitudes():
    db = get_mongo_db()
    if db is None:
        return []
    try:
        return list(db.solicitudes.find({'estado': 'pendiente'}).sort('fecha_solicitud', -1))
    except Exception as e:
        print(f"[MONGO ERROR] Error obteniendo solicitudes: {e}")
        return []

def get_solicitud_by_id(id_solicitud):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return db.solicitudes.find_one({'_id': ObjectId(id_solicitud)})
    except Exception as e:
        return None

def update_solicitud_status(id_solicitud, estado):
    db = get_mongo_db()
    if db is None:
        return False
    try:
        res = db.solicitudes.update_one({'_id': ObjectId(id_solicitud)}, {'$set': {'estado': estado}})
        return res.modified_count > 0
    except Exception as e:
        return False

def insert_asignacion_sql(data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            query = """
            INSERT INTO asignaciones (id_equipo, usuario_uid, rol_assigned, fecha_desde, fecha_hasta, activa)
            VALUES (%s, %s, %s, %s, %s, 1)
            """
            cursor.execute(query, (
                data['id_equipo'],
                data['usuario_uid'],
                data['rol_assigned'],
                data['fecha_desde'],
                data['fecha_hasta']
            ))
            
            query_eq = "UPDATE equipos SET estado = 'asignado' WHERE id_equipo = %s"
            cursor.execute(query_eq, (data['id_equipo'],))
            return True
    except Exception as e:
        print(f"[SQL ERROR] Error inserting asignacion: {e}")
        return False
    finally:
        conn.close()

def get_equipos_activos():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute("SELECT id_equipo, codigo_inventario, numero_banco FROM equipos WHERE estado = 'activo' ORDER BY id_equipo")
            return cursor.fetchall()
    except Exception as e:
        return []
    finally:
        conn.close()
