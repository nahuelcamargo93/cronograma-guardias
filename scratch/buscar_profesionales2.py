import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

nombres = [
    "DURAN JAZMIN",
    "PEREIRA CRISTINA",
    "TULA DAIANA",
    "ALCARAZ ELIANA",
    "ALCARAZ FRANCISCO",
    "GUIÑAZU KARINA",
    "MEDINA LAURA",
    "ORTIZ LAURA",
    "GOMEZ LOURDES",
    "GOMES STHEFANIA",
    "OLGUIN LUCIA",
    "ALBELO TANIA",
    "FERNANDEZ YESICA",
    "SUAREZ JESICA"
]

print("--- Searching for professionals ---")
for nombre in nombres:
    cursor.execute("SELECT nombre, servicio_id, activo FROM personal WHERE nombre = ?", (nombre,))
    exact = cursor.fetchone()
    if exact:
        print(f"EXACT MATCH: {exact[0]} | Servicio: {exact[1]} | Activo: {exact[2]}")
    else:
        partes = nombre.split()
        query_parts = " AND ".join(["nombre LIKE ?"] * len(partes))
        params = [f"%{p}%" for p in partes]
        cursor.execute(f"SELECT nombre, servicio_id, activo FROM personal WHERE {query_parts}", params)
        partials = cursor.fetchall()
        if partials:
            print(f"PARTIAL MATCHES FOR '{nombre}':")
            for p in partials:
                print(f"  - {p[0]} | Servicio: {p[1]} | Activo: {p[2]}")
        else:
            print(f"NO MATCH FOR '{nombre}'")

conn.close()
