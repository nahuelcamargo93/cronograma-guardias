import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438
names = ["Garcia, Luciano", "Toledo, Andrea", "Franco, Leandro", "Moyano, Fernando"]

for name in names:
    print(f"\n=== GUARDIAS PARA {name} ===")
    rows = conn.execute(
        "SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = ? AND nombre = ? ORDER BY fecha",
        (crono_id, name)
    ).fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]} ({row[2]} hs)")
        
conn.close()
