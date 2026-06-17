import sqlite3
from database.connection import DB_PATH

def check_staff():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre, p.rol, p.activo, 
               (SELECT GROUP_CONCAT(pts.nombre) 
                FROM personal_puestos pp 
                JOIN puestos pts ON pp.puesto_id = pts.id 
                WHERE pp.personal_nombre = p.nombre) as puestos
        FROM personal p 
        WHERE p.servicio_id = 4
    """)
    rows = cursor.fetchall()
    print("Personal del Servicio 4:")
    for row in rows:
        print(f"  - Nombre: {row[0]}, Rol: {row[1]}, Activo: {row[2]}, Puestos: {row[3]}")
    conn.close()

if __name__ == "__main__":
    check_staff()
