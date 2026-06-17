import sqlite3
import json

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- REGLAS ACTIVAS POR SERVICIO ---")
    rows = cursor.execute("""
        SELECT sr.servicio_id, s.nombre, sr.codigo_regla, sr.parametros_json, sr.activo
        FROM servicios_reglas sr
        JOIN servicios s ON sr.servicio_id = s.id
        WHERE sr.activo = 1
        ORDER BY sr.servicio_id, sr.codigo_regla
    """).fetchall()
    
    for row in rows:
        print(f"Servicio ID: {row[0]} ({row[1]}) | Regla: {row[2]} | Params: {row[3]}")
        
    conn.close()

if __name__ == "__main__":
    main()
