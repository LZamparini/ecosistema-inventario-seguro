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
