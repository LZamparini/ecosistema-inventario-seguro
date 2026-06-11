import sys
import pytds
import config
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"Probando conexion SQL Server a {config.SQL_SERVER_HOST}:{config.SQL_SERVER_PORT}")
print(f"Usuario: {config.SQL_SERVER_USER}")
print(f"Base de datos: {config.SQL_SERVER_DATABASE}")

try:
    conn = pytds.connect(
        server=config.SQL_SERVER_HOST,
        port=config.SQL_SERVER_PORT,
        user=config.SQL_SERVER_USER,
        password=config.SQL_SERVER_PASSWORD,
        database=config.SQL_SERVER_DATABASE,
        autocommit=True,
        login_timeout=5
    )
    print("CONEXION EXITOSA A SQL SERVER")
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"Versión de SQL Server: {row[0]}")
        
        print("\nConsultando aulas:")
        cursor.execute("SELECT id_aula, nombre, tipo FROM aulas")
        for r in cursor.fetchall():
            print(f"- ID: {r[0]}, Nombre: {r[1]}, Tipo: {r[2]}")
            
    conn.close()
except Exception as e:
    print(f"ERROR DE CONEXION: {e}")
