import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

buscar_nombres = [
    "NIEVAS CARLA",
    "CASTRO LUCIANO",
    "QUEVEDO CELESTE",
    "PEREIRA CRISTINA"
]

print("--- Nombres encontrados en 'personal' ---")
real_names = {}
for nom in buscar_nombres:
    parts = nom.split()
    query = "SELECT nombre FROM personal WHERE " + " AND ".join(["nombre LIKE ?"]*len(parts))
    params = [f"%{p}%" for p in parts]
    cursor.execute(query, params)
    rows = cursor.fetchall()
    real_names[nom] = [r[0] for r in rows]
    print(f"{nom} matches in 'personal': {real_names[nom]}")

# Feriados
cursor.execute("SELECT fecha, descripcion FROM feriados;")
feriados = {r[0]: r[1] for r in cursor.fetchall()}

# Busquemos los cronogramas
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas;")
cronogramas = {r[0]: r for r in cursor.fetchall()}

print("\n--- Guardias en feriados por persona ---")
for nom, matches in real_names.items():
    print(f"\nPersona: {nom}")
    if not matches:
        print("  No se encontró coincidencia en 'personal'.")
        continue
    for m in matches:
        cursor.execute("""
            SELECT cronograma_id, fecha, turno, horas, servicio_id
            FROM guardias
            WHERE nombre = ?
            ORDER BY fecha;
        """, (m,))
        guardias_rows = cursor.fetchall()
        
        # Filtramos las de feriados
        feriados_trabajados = []
        for g in guardias_rows:
            c_id, fecha, turno, horas, s_id = g
            if fecha in feriados:
                feriados_trabajados.append((c_id, fecha, feriados[fecha], turno, horas))
        
        if not feriados_trabajados:
            print(f"  {m}: No tiene guardias asignadas en feriados.")
        else:
            print(f"  {m}:")
            # Agrupar por cronograma para mayor claridad
            for c_id, fecha, desc, turno, horas in feriados_trabajados:
                c_info = cronogramas.get(c_id, (c_id, "Desconocido", "Desconocido", "", ""))
                c_periodo = f"{c_info[1]} a {c_info[2]}"
                c_estado = c_info[4]
                print(f"    - [{c_estado}] Cronograma ID {c_id} ({c_periodo}): {fecha} ({desc}) | Turno {turno} | Horas {horas}")

conn.close()
