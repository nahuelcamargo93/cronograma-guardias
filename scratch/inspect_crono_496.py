import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 496
names = ["Garcia, Luciano", "Toledo, Andrea"]

# Check crono 496 dates
crono = conn.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
if crono:
    print(f"=== CRONOGRAMA 496 ({crono[0]} a {crono[1]}) ===")
else:
    print("Cronograma 496 no encontrado")

for name in names:
    print(f"\n=== GUARDIAS PARA {name} ===")
    rows = conn.execute(
        "SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = ? AND nombre = ? ORDER BY fecha",
        (crono_id, name)
    ).fetchall()
    for row in rows:
        print(f"  {row[0]}: {row[1]} ({row[2]} hs)")
        
conn.close()
