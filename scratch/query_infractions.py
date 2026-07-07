import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT codigo_regla, detalle 
        FROM infracciones_debug 
        WHERE cronograma_id = 523 
          AND codigo_regla IN ('COBERTURA_DINAMICA', 'ESQUEMA_SEMANAL_ENFERMERIA', 'FINDE_POST_LICENCIA', 'FIN_LICENCIA')
    """)
    rows = cur.fetchall()
    print(f"Total rows: {len(rows)}")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
