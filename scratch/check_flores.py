import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"

def run():
    conn = sqlite3.connect(DB_PATH)
    print("--- Datos de Flores en la tabla 'personal' ---")
    cursor = conn.execute("SELECT nombre, servicio_id, activo FROM personal WHERE nombre LIKE '%Flores%'")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Cronogramas aprobados ---")
    cursor = conn.execute("SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas WHERE estado = 'aprobado'")
    cronos = cursor.fetchall()
    for c in cronos:
        print(c)
        
    print("\n--- Bloques de Finde Largo ---")
    cursor = conn.execute("SELECT id, cronograma_id, fecha_inicio, fecha_fin, tipo FROM bloques_finde_largo")
    for b in cursor.fetchall():
        print(b)
        
    print("\n--- Guardias de Flores en fines de semana ---")
    cursor = conn.execute("""
        SELECT g.nombre, g.fecha, g.turno, g.es_finde, c.id, c.estado 
        FROM guardias g 
        JOIN cronogramas c ON g.cronograma_id = c.id
        WHERE g.nombre LIKE '%Flores%' AND g.es_finde = 1
    """)
    for g in cursor.fetchall():
        print(g)

    conn.close()

if __name__ == "__main__":
    run()
