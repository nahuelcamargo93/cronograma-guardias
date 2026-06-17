import sqlite3
from datetime import date, timedelta

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the latest cronograma
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas FROM cronogramas ORDER BY id DESC LIMIT 1")
crono = cursor.fetchone()
print("LATEST CRONOGRAMA IN DB:", crono)

if crono:
    crono_id = crono[0]
    fecha_inicio = crono[1]
    fecha_fin = crono[2]
    
    # Check what service_id was this cronograma for
    # Let's find personal from guardias in this cronograma to see their service_id
    cursor.execute("""
        SELECT DISTINCT p.servicio_id 
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ?
    """, (crono_id,))
    services = cursor.fetchall()
    print("Service IDs for this cronograma:", [s[0] for s in services])
    
    # Get all licencias for BORIA MAYRA during this period
    cursor.execute("""
        SELECT tipo, fecha_inicio, fecha_fin 
        FROM licencias 
        WHERE nombre = 'BORIA MAYRA' 
          AND (fecha_inicio <= ? AND fecha_fin >= ?)
    """, (fecha_fin, fecha_inicio))
    licencias = cursor.fetchall()
    print("Licencias for BORIA MAYRA during cronograma:", licencias)

    # Get all guardias for BORIA MAYRA in this cronograma
    cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = ? AND nombre = 'BORIA MAYRA'
        ORDER BY fecha
    """, (crono_id,))
    guardias = cursor.fetchall()
    print("Guardias for BORIA MAYRA in this cronograma:", len(guardias))
    for g in guardias:
        print(f"  {g[0]}: {g[1]} ({g[2]}h)")

    # Check if she got any FLR assigned in flr_asignados
    cursor.execute("""
        SELECT fecha_inicio, fecha_fin 
        FROM flr_asignados 
        WHERE cronograma_id = ? AND nombre = 'BORIA MAYRA'
    """, (crono_id,))
    flr_asig = cursor.fetchall()
    print("FLRs assigned to BORIA MAYRA in flr_asignados:", flr_asig)

    # Check all employees with no FLRs assigned in this cronograma
    # Find all distinct names in guardias for this cronograma
    cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = ?", (crono_id,))
    empleados = [r[0] for r in cursor.fetchall()]
    
    print("\nFLR status for all employees in this cronograma:")
    for emp in empleados:
        cursor.execute("SELECT COUNT(*) FROM flr_asignados WHERE cronograma_id = ? AND nombre = ?", (crono_id, emp))
        count = cursor.fetchone()[0]
        print(f"  {emp}: {count} FLR(s)")

conn.close()
