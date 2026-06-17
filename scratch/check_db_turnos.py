import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    rows = conn.execute("SELECT id, nombre, hora_inicio, horas, dias_semana FROM turnos_config WHERE servicio_id = 1").fetchall()
    print("--- Turnos de Kinesiología en turnos_config ---")
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    run()
