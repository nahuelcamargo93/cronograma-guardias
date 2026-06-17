import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Nombres a buscar
buscar_nombres = [
    "NIEVAS CARLA",
    "CASTRO LUCIANO",
    "QUEVEDO CELESTE",
    "PEREIRA CRISTINA"
]

print("Búsqueda en la tabla 'personal':")
for nom in buscar_nombres:
    cursor.execute("SELECT nombre, rol, categoria, servicio_id FROM personal WHERE nombre LIKE ?;", (f"%{nom}%",))
    rows = cursor.fetchall()
    print(f"  {nom} -> {rows}")

print("\nBúsqueda de nombres distintos en 'guardias' similar a los buscados:")
for nom in buscar_nombres:
    parts = nom.split()
    # busquemos por el apellido o nombre
    for part in parts:
        cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE nombre LIKE ?;", (f"%{part}%",))
        rows = cursor.fetchall()
        if rows:
            print(f"  {part} en guardias -> {rows}")

# Traer todos los feriados
cursor.execute("SELECT fecha, descripcion FROM feriados ORDER BY fecha;")
feriados = {r[0]: r[1] for r in cursor.fetchall()}
print(f"\nTotal feriados en la DB: {len(feriados)}")

# Mostrar información de los cronogramas existentes
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas;")
cronogramas = cursor.fetchall()
print("\nCronogramas:")
for c in cronogramas:
    print(f"  ID {c[0]}: {c[1]} a {c[2]} ({c[3]}, Estado: {c[4]})")

# Busquemos las guardias de estas personas que caigan en feriados
print("\nGuardias en días feriados:")
for nom in buscar_nombres:
    parts = nom.split()
    # Buscamos coincidencias en guardias
    # Usamos el apellido principal
    apellido = parts[0]
    cursor.execute("""
        SELECT g.cronograma_id, g.nombre, g.fecha, g.turno, g.horas, s.nombre
        FROM guardias g
        JOIN servicios s ON g.servicio_id = s.id
        WHERE g.nombre LIKE ? ORDER BY g.fecha;
    """, (f"%{apellido}%",))
    guardias_rows = cursor.fetchall()
    
    guardias_en_feriado = []
    for row in guardias_rows:
        cron_id, emp_nombre, fecha, turno, horas, serv_nombre = row
        if fecha in feriados:
            guardias_en_feriado.append((cron_id, emp_nombre, fecha, feriados[fecha], turno, horas, serv_nombre))
            
    print(f"\n  Resultados para {nom}:")
    if not guardias_en_feriado:
        print("    Ninguna guardia en feriado.")
    for gef in guardias_en_feriado:
        print(f"    - Cronograma ID {gef[0]} ({gef[6]}): Fecha {gef[2]} ({gef[3]}) | Turno: {gef[4]} | Horas: {gef[5]}")

conn.close()
