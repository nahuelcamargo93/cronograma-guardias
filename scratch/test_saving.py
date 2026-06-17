import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import datetime
from ortools.sat.python import cp_model

print("Ejecutando optimización en modo debug para testear el guardado...")
res = main.ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", modo_debug=True)
print("Resultado retornado por ejecutar_optimizacion:", res)

# Verificar en la BD el cronograma que se acaba de crear
cid = res.get("cronograma_id")
if cid:
    import sqlite3
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, creado_en FROM cronogramas WHERE id = ?", (cid,))
    print("Cronograma creado:", cursor.fetchone())
    
    cursor.execute("SELECT COUNT(*) FROM guardias WHERE cronograma_id = ?", (cid,))
    print("Guardias guardadas:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM flr_asignados WHERE cronograma_id = ?", (cid,))
    print("FLRs guardados:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM infracciones_debug WHERE cronograma_id = ?", (cid,))
    print("Infracciones guardadas:", cursor.fetchone()[0])
    
    conn.close()
