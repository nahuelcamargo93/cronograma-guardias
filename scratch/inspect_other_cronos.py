import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    crono_ids = [152, 166, 167, 168]
    for cid in crono_ids:
        print(f"\n=== CRONOGRAMA ID {cid} ===")
        rows = cursor.execute("""
            SELECT nombre, fecha, turno, horas 
            FROM guardias 
            WHERE cronograma_id = ? 
              AND fecha IN ('2026-06-13', '2026-06-15')
              AND (nombre LIKE '%Garcia%' OR nombre LIKE '%N%' OR nombre LIKE '%Nuñez%')
            ORDER BY fecha, nombre
        """, (cid,)).fetchall()
        for r in rows:
            print(f"Name: {repr(r[0])} | Fecha: {r[1]} | Turno: {r[2]} | Horas: {r[3]}")
            
    conn.close()

if __name__ == '__main__':
    main()
