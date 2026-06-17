import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import sqlite3
import json
import main as main_module
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def inspect_db_state():
    conn = sqlite3.connect(os.path.join(project_root, "cronograma_inteligente.db"))
    cursor = conn.cursor()
    
    print("=== Reglas del Servicio 3 en la base de datos ===")
    cursor.execute("""
        SELECT id, codigo_regla, activo, parametros_json 
        FROM servicios_reglas
        WHERE servicio_id = 3
    """)
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Código: {row[1]} | Activo: {row[2]} | Params: {row[3]}")
        
    print("\n=== Reglas Individuales de Personal del Servicio 3 ===")
    cursor.execute("""
        SELECT pr.id, pr.personal_nombre, pr.codigo_regla, pr.activo, pr.parametros_json
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 3 AND pr.activo = 1
    """)
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Persona: {row[1]} | Regla: {row[2]} | Activo: {row[3]} | Params: {row[4]}")
        
    conn.close()

if __name__ == "__main__":
    inspect_db_state()
