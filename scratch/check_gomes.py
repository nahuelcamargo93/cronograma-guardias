import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

name = "GOMES STHEFANIA"
crono_id = 257

# Buscar el último cronograma aprobado antes de 2026-07-01 para el servicio 2
cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE c.estado = 'aprobado' AND c.fecha_inicio < '2026-07-01' AND p.servicio_id = 2
    ORDER BY c.fecha_inicio DESC
    LIMIT 1
""")
row_cr = cursor.fetchone()
if row_cr:
    ultimo_crono_id, fecha_inicio_prev = row_cr
    print(f"Último cronograma aprobado: ID {ultimo_crono_id} (Inicio: {fecha_inicio_prev})")
    
    print("\n=== HISTORIAL DE GOMES STHEFANIA (Junio) ===")
    cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = ? AND nombre = ? AND fecha >= '2026-06-29' AND fecha <= '2026-06-30'
    """, (ultimo_crono_id, name))
    for r in cursor.fetchall():
        print(r)
else:
    print("No se encontró cronograma aprobado previo.")

print("\n=== ASIGNACIONES EN CRONOGRAMA 257 (Julio, semana 1) ===")
cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre = ? AND fecha >= '2026-07-01' AND fecha <= '2026-07-05'
""", (crono_id, name))
for r in cursor.fetchall():
    print(r)

conn.close()
