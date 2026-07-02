import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

def print_query(title, query, params=()):
    print("="*60)
    print(title)
    print("="*60)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    for r in rows:
        print(r)
    print()

# 1. Guardias de Albelo Tania, Guiñazu Karina, Mañe Lorena en julio 2026 (cronograma aprobado)
print_query(
    "Guardias de Albelo Tania, Guiñazu Karina, Mañe Lorena en julio 2026",
    "SELECT g.nombre, g.fecha, g.turno FROM guardias g JOIN cronogramas c ON g.cronograma_id = c.id WHERE (g.nombre LIKE '%ALBELO TANIA%' OR g.nombre LIKE '%GUIÑAZU KARINA%' OR g.nombre LIKE '%MAÑE LORENA%') AND g.fecha LIKE '2026-07%' AND c.estado = 'aprobado' ORDER BY g.nombre, g.fecha"
)

# 3. Licencias de Ortiz Laura y Alcaraz Eliana en julio/agosto 2026
print_query(
    "Licencias de Ortiz Laura y Alcaraz Eliana",
    "SELECT nombre, fecha_inicio, fecha_fin, tipo FROM licencias WHERE nombre LIKE '%ORTIZ LAURA%' OR nombre LIKE '%ALCARAZ ELIANA%' ORDER BY nombre, fecha_inicio"
)

conn.close()
