import sqlite3
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 435

print("=== ALL EMPLOYEES AND THEIR WEEKEND SHIFTS ===")
rows = conn.execute(
    "SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id = ?", (crono_id,)
).fetchall()

counts = {}
for name, f_str, turno in rows:
    dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    wd = dt.weekday()
    if wd in (5, 6):
        counts.setdefault(name, []).append((f_str, wd, turno))

for name, shifts in sorted(counts.items()):
    print(f"{name}: {len(shifts)} shifts")
    for s in shifts:
        print(f"  {s[0]} (WD {s[1]}): {s[2]}")

print("\n=== EMPLOYEES WITH NO WEEKEND SHIFTS ===")
all_names = [r[0] for r in conn.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND activo = 1").fetchall()]
for name in sorted(all_names):
    if name not in counts:
        print(name)

conn.close()
