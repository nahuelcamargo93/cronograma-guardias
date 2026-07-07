import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection

with get_connection() as conn:
    rows = conn.execute("""
        SELECT nombre, categoria, rol FROM personal 
        WHERE servicio_id = 4 AND nombre IN (
            'FERNANDEZ Claudia Elizabeth', 
            'QUINTANA Felipe Gabriel', 
            'SUÑER Mara Tatiana', 
            'BRIZUELA Irma'
        )
    """).fetchall()
    print("Personal Info:")
    for row in rows:
        print(row)
        
    puestos = conn.execute("""
        SELECT pp.personal_nombre, p.nombre, pp.es_primario 
        FROM personal_puestos pp
        JOIN puestos p ON pp.puesto_id = p.id
        WHERE pp.personal_nombre IN (
            'FERNANDEZ Claudia Elizabeth', 
            'QUINTANA Felipe Gabriel', 
            'SUÑER Mara Tatiana', 
            'BRIZUELA Irma'
        )
    """).fetchall()
    print("\nPersonal Puestos Info:")
    for row in puestos:
        print(row)
        
    reglas = conn.execute("""
        SELECT personal_nombre, codigo_regla, parametros_json 
        FROM personal_reglas
        WHERE personal_nombre IN (
            'FERNANDEZ Claudia Elizabeth', 
            'QUINTANA Felipe Gabriel', 
            'SUÑER Mara Tatiana', 
            'BRIZUELA Irma'
        )
    """).fetchall()
    print("\nPersonal Reglas Info:")
    for row in reglas:
        print(row)
