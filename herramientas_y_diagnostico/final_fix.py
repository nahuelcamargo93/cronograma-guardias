import sqlite3

def get_db():
    return sqlite3.connect('cronograma_inteligente.db')

def update_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Truncate tables
    cursor.execute("DELETE FROM licencias")
    cursor.execute("DELETE FROM turnos_ajustes")
    print("Truncated 'licencias' and 'turnos_ajustes' tables.")

    # 2. Mapping
    mapping = {
        "Camargo nahuel": "Lic. Camargo N.",
        "Garcia Luciano": "Lic. Garcia",
        "Giacoppo Veronica": "Lic. Giaccoppo",
        "Sosa Nicolas": "Lic. Sosa",
        "Juarez Eduardo": "Lic. Juarez",
        "Guardia Gabriel": "Lic. Guardia",
        "Toleado Andrea": "Lic. Toledo",
        "Moyano Fernando": "Lic. Moyano",
        "Emiliano Marino": "Lic. Marino",
        "Bruno Mesa": "Lic. Mesa",
        "Danae Syiriani": "Lic. Syriani",
        "Franco Leonforte": "Lic. Leonforte",
        "Guzman, Ariel": "Lic. Guzman",
        "Flores": "Lic. Flores",
        "Franco, Leandro": "Lic. Franco",
        "Melisa Coniglio": "Lic. Coniglio",
        "Lucas Welch": "Lic. Welch",
        "Elizabeth Espinosa": "Lic. Espinosa",
        "Nicolas Vander": "Lic. Vander",
        "Eric Vivas": "Lic. Vivas"
    }

    # 3. New LPP data (Year 2026)
    lpps = [
        ("Camargo nahuel", "2026-04-06", "2026-04-19"),
        ("Garcia Luciano", "2026-05-04", "2026-05-17"),
        ("Giacoppo Veronica", "2026-05-04", "2026-05-17"),
        ("Sosa Nicolas", "2026-05-04", "2026-05-17"),
        ("Juarez Eduardo", "2026-05-18", "2026-06-01"),
        ("Guardia Gabriel", "2026-05-18", "2026-06-01"),
        ("Toleado Andrea", "2026-05-18", "2026-06-01"),
        ("Moyano Fernando", "2026-06-01", "2026-06-14"),
        ("Emiliano Marino", "2026-06-01", "2026-06-14"),
        ("Bruno Mesa", "2026-06-01", "2026-06-14"),
        ("Danae Syiriani", "2026-06-01", "2026-06-14"),
        ("Franco Leonforte", "2026-06-01", "2026-06-14"),
        ("Guzman, Ariel", "2026-05-25", "2026-06-07"),
        ("Flores", "2026-05-25", "2026-06-07"),
        ("Franco, Leandro", "2026-06-08", "2026-06-21"),
        ("Melisa Coniglio", "2026-06-15", "2026-06-29"),
        ("Lucas Welch", "2026-06-15", "2026-06-29"),
        ("Elizabeth Espinosa", "2026-06-15", "2026-06-29"),
        ("Nicolas Vander", "2026-06-15", "2026-06-29"),
        ("Eric Vivas", "2026-06-15", "2026-06-29")
    ]

    for user_name, start, end in lpps:
        db_name = mapping.get(user_name)
        if db_name:
            cursor.execute("INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin) VALUES (?, 'LPP', ?, ?)", (db_name, start, end))
        else:
            print(f"Warning: Could not map {user_name}")

    conn.commit()
    print(f"Inserted {len(lpps)} licenses.")
    conn.close()

if __name__ == "__main__":
    update_db()
