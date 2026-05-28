import sqlite3
import datetime

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all cronogramas for service 3
# Since cronogramas don't have a direct service_id column, let's identify them.
# We can join with guardias to see which service_id the personal belong to.
cur.execute("""
    SELECT DISTINCT g.cronograma_id, c.fecha_inicio, c.fecha_fin, c.creado_en
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 3
    ORDER BY g.cronograma_id DESC
""")
cronos = cur.fetchall()

print("Recent Cronogramas for Service 3:")
for cr in cronos:
    print(f"ID: {cr[0]} | Start: {cr[1]} | End: {cr[2]} | Created: {cr[3]}")
    
    # Check Fridays for Matricadi in this cronograma
    cur.execute("""
        SELECT fecha, turno
        FROM guardias
        WHERE cronograma_id = ? AND (nombre LIKE '%Matricardi%' OR nombre LIKE '%Matricadi%')
        ORDER BY fecha
    """, (cr[0],))
    guards = cur.fetchall()
    
    fridays = []
    for g in guards:
        dt = datetime.date.fromisoformat(g[0])
        if dt.weekday() == 4:
            fridays.append(f"{g[0]} ({g[1]})")
            
    print(f"  Matricadi: {len(fridays)} Fridays: {fridays}")
    print(f"  All shifts for Matricadi: {guards}")

conn.close()
