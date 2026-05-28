import sqlite3
from datetime import datetime, date, timedelta

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()

# Get all guardias for cronograma 232
cur.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id = 232 ORDER BY fecha, nombre")
rows = cur.fetchall()

print("--- GUARDIAS ON SPECIFIC SUNDAYS IN JULY 2026 (d = 4, 11, 18, 25) ---")
target_dates = {"2026-07-05", "2026-07-12", "2026-07-19", "2026-07-26"}

worked_by_emp = {}
for r in rows:
    if r[1] in target_dates:
        print(f"{r[1]} (Sunday): {r[0]} worked {r[2]}")
        worked_by_emp[r[0]] = worked_by_emp.get(r[0], 0) + 1

print("\n--- SUMMARY OF SUNDAYS WORKED BY EMPLOYEES ---")
for emp, count in sorted(worked_by_emp.items()):
    print(f"{emp}: {count} Sunday(s) worked")

conn.close()
