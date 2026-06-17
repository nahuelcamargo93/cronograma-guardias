import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, servicio_id, rol FROM personal WHERE nombre LIKE '%garcia%' OR nombre LIKE '%luciano%'")
    rows = cursor.fetchall()
    print("Coincidencias en personal:")
    for r in rows:
        print(f"Nombre: '{r[0]}', Servicio: {r[1]}, Rol: '{r[2]}'")
    conn.close()

if __name__ == "__main__":
    main()
