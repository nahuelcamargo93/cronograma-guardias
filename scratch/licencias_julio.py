import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

buscar_nombres = [
    "NIEVAS CARLA",
    "CASTRO LUCIANO",
    "QUEVEDO CELESTE",
    "PEREIRA CRISTINA"
]

print("Licencias en Julio 2026:")
for nom in buscar_nombres:
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin, tipo 
        FROM licencias 
        WHERE nombre = ? AND (fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01')
    """, (nom,))
    rows = cursor.fetchall()
    print(f"  {nom}: {rows}")

conn.close()
