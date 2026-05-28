import sys
sys.path.insert(0, 'c:/Users/asus/Desktop/Ryoko/cronograma_inteligente')

import sqlite3
import json
from database import queries as db_queries
from database.data_loader import obtener_empleados

def inspect():
    conn = sqlite3.connect('cronograma_inteligente.db')
    c = conn.cursor()
    
    names = ['Aguilera Graciela', 'Garcia Rodriguez, Maria Eugenia.']
    for name in names:
        print(f"\n=================== INSPECTING: {name} ===================")
        # 1. Personal table entry
        c.execute("SELECT * FROM personal WHERE nombre = ?", (name,))
        print("Personal table:", c.fetchone())
        
        # 2. Personal rules
        c.execute("SELECT * FROM personal_reglas WHERE personal_nombre = ? AND activo = 1", (name,))
        print("Personal rules:")
        for r in c.fetchall():
            print("  ", r)
            
        # 3. Personal rule adjustments
        c.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = ? AND activo = 1", (name,))
        print("Personal rule adjustments:")
        for r in c.fetchall():
            print("  ", r)

        # 4. Puestos habilitados
        c.execute("""
            SELECT p.nombre, pp.es_primario 
            FROM personal_puestos pp 
            JOIN puestos p ON pp.puesto_id = p.id 
            WHERE pp.personal_nombre = ?
        """, (name,))
        print("Puestos habilitados:")
        for r in c.fetchall():
            print("  ", r)

inspect()
