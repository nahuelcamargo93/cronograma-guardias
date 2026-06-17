import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Obtener el último cronograma del servicio 2
row = cursor.execute("""
    SELECT c.id, c.fecha_inicio, c.fecha_fin
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 2
    ORDER BY c.id DESC
    LIMIT 1
""").fetchone()

if row:
    crono_id, fi, ff = row
    print(f"=== Último Cronograma Servicio 2: ID {crono_id} ({fi} a {ff}) ===")
    
    # Consultar guardias de Melina Astudillo
    print("\nGuardias de ASTUDILLO MELINA:")
    guardias = cursor.execute("""
        SELECT fecha, turno
        FROM guardias
        WHERE cronograma_id = ? AND nombre = 'ASTUDILLO MELINA'
        ORDER BY fecha
    """, (crono_id,)).fetchall()
    
    for g in guardias:
        print(f"  Fecha: {g[0]}, Turno: {g[1]}")
        
    # Consultar FLRs asignados a Melina Astudillo
    print("\nFLRs asignados a ASTUDILLO MELINA:")
    flrs = cursor.execute("""
        SELECT fecha_inicio, fecha_fin
        FROM flr_asignados
        WHERE cronograma_id = ? AND nombre = 'ASTUDILLO MELINA'
    """, (crono_id,)).fetchall()
    for flr in flrs:
        print(f"  Inicio: {flr[0]}, Fin: {flr[1]}")
else:
    print("No se encontró ningún cronograma para el servicio 2.")

conn.close()
