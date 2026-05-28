import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get total hours worked by all employees in service 3
cur.execute("""
    SELECT p.nombre, p.regimen_trabajo, SUM(g.horas)
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 216 AND p.servicio_id = 3
    GROUP BY p.nombre
    ORDER BY SUM(g.horas) DESC
""")
rows = cur.fetchall()

total_hours = 0
total_shifts = 0
print("Hours and shifts assigned per employee in Cronograma 216:")
for nombre, regimen, horas in rows:
    regimen_str = str(regimen) if regimen is not None else "None"
    print(f"  {nombre:30s} | Regimen: {regimen_str:10s} | Hours: {horas} | Shifts: {horas/24.0:.1f}")
    total_hours += horas
    total_shifts += (horas / 24.0)

print(f"\nTotal Hours Assigned: {total_hours}")
print(f"Total Shifts Assigned (in 24h equivalent): {total_shifts}")

conn.close()
