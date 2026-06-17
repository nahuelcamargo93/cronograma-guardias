import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

buscar_nombres = [
    "NIEVAS CARLA",
    "CASTRO LUCIANO",
    "QUEVEDO CELESTE",
    "PEREIRA CRISTINA"
]

# 1. Obtener nombres exactos en la tabla personal
real_names = {}
for nom in buscar_nombres:
    parts = nom.split()
    query = "SELECT nombre, servicio_id FROM personal WHERE " + " AND ".join(["nombre LIKE ?"]*len(parts))
    params = [f"%{p}%" for p in parts]
    cursor.execute(query, params)
    rows = cursor.fetchall()
    real_names[nom] = rows
    print(f"Búsqueda {nom} -> {rows}")

# 2. Obtener todos los feriados
cursor.execute("SELECT fecha, descripcion FROM feriados;")
feriados = {r[0]: r[1] for r in cursor.fetchall()}

# 3. Obtener todos los cronogramas
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas;")
cronogramas = {r[0]: r for r in cursor.fetchall()}

# 4. Obtener servicios
cursor.execute("SELECT id, nombre FROM servicios;")
servicios = {r[0]: r[1] for r in cursor.fetchall()}

# Vamos a escribir un archivo markdown con todos los detalles
with open("scratch/resultados_feriados.md", "w", encoding="utf-8") as f:
    f.write("# Resultados de Guardias en Feriados\n\n")
    
    for nom, matches in real_names.items():
        f.write(f"## Persona: {nom}\n")
        if not matches:
            f.write("No se encontraron coincidencias en la base de datos de personal.\n\n")
            continue
            
        for db_name, s_id in matches:
            f.write(f"### Nombre en BD: `{db_name}` (Servicio: {servicios.get(s_id, 'Desconocido')})\n")
            
            # Buscar guardias
            cursor.execute("""
                SELECT cronograma_id, fecha, turno, horas
                FROM guardias
                WHERE nombre = ?
                ORDER BY fecha;
            """, (db_name,))
            guardias = cursor.fetchall()
            
            feriados_trabajados = []
            for g in guardias:
                c_id, fecha, turno, horas = g
                if fecha in feriados:
                    feriados_trabajados.append((c_id, fecha, feriados[fecha], turno, horas))
            
            if not feriados_trabajados:
                f.write("No trabaja ningún feriado en los cronogramas registrados.\n\n")
                continue
                
            # Agrupar por cronograma
            c_groups = {}
            for c_id, fecha, desc, turno, horas in feriados_trabajados:
                c_groups.setdefault(c_id, []).append((fecha, desc, turno, horas))
                
            f.write("Guardias asignadas en feriados:\n\n")
            # Ordenar por cronograma ID descendente (más recientes primero)
            for c_id in sorted(c_groups.keys(), reverse=True):
                c_info = cronogramas.get(c_id, (c_id, "Desconocido", "Desconocido", "", "Desconocido"))
                f.write(f"#### Cronograma ID {c_id} (Período: {c_info[1]} a {c_info[2]} | Notas: {c_info[3]} | Estado: {c_info[4]})\n")
                f.write("| Fecha | Feriado | Turno | Horas |\n")
                f.write("| --- | --- | --- | --- |\n")
                for fecha, desc, turno, horas in c_groups[c_id]:
                    f.write(f"| {fecha} | {desc} | {turno} | {horas} |\n")
                f.write("\n")
            f.write("\n")

print("Se ha generado el reporte completo en scratch/resultados_feriados.md")
conn.close()
