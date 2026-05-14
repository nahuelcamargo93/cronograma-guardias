import sqlite3
import json

def check_turnos():
    conn = sqlite3.connect('cronograma_inteligente.db')
    rows = conn.execute("SELECT id, nombre, hora_inicio, hora_fin, horas FROM turnos_config WHERE servicio_id = 2").fetchall()
    print("Turnos Service 2:")
    for r in rows:
        print(r)
    
    rows = conn.execute("SELECT * FROM demanda_config WHERE servicio_id = 2").fetchall()
    print("\nDemanda Service 2:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    check_turnos()
