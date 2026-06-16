"""
db.py — Módulo para conectar a SQL Server usando pymssql.
"""

import pymssql
import config

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
