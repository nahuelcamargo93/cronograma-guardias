import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import sqlite3

def inspect_demanda():
    conn = sqlite3.connect(os.path.join(project_root, "cronograma_inteligente.db"))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT dc.id, p.nombre as puesto, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 3
    """)
    print("=== Configuración de Demanda del Servicio 3 ===")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Puesto: {row[1]} | Tipo Día: {row[2]} | Ventana: {row[3]}-{row[4]} | Min: {row[5]} | Max: {row[6]}")
        
    conn.close()

if __name__ == "__main__":
    inspect_demanda()
