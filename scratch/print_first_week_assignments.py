import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

def print_assignments(crono_id):
    print(f"\n=== Asignaciones del Cronograma {crono_id} ===")
    cursor.execute("""
        SELECT fecha, turno, nombre 
        FROM guardias 
        WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-01' AND '2026-07-03'
        ORDER BY fecha, turno, nombre
    """, (crono_id,))
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]:<12} | {r[2]}")

print_assignments(499) # Debug soft
print_assignments(500) # Normal viable (con crono 492 en borrador)

conn.close()
