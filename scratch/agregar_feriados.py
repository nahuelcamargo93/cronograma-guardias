import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

FERIADOS_2026 = [
    # Nacionales Inamovibles
    ("2026-01-01", "Año Nuevo"),
    ("2026-02-16", "Carnaval"),
    ("2026-02-17", "Carnaval"),
    ("2026-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia"),
    ("2026-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas"),
    ("2026-04-03", "Viernes Santo"),
    ("2026-05-01", "Día del Trabajador"),
    ("2026-05-25", "Día de la Revolución de Mayo"),
    ("2026-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano"),
    ("2026-07-09", "Día de la Independencia"),
    ("2026-12-08", "Día de la Inmaculada Concepción de María"),
    ("2026-12-25", "Navidad"),
    
    # Nacionales Trasladables (con fecha efectiva de traslado para el 2026)
    ("2026-06-15", "Paso a la Inmortalidad del Gral. Martín Miguel de Güemes"),
    ("2026-08-17", "Paso a la Inmortalidad del Gral. José de San Martín"),
    ("2026-10-12", "Día del Respeto a la Diversidad Cultural"),
    ("2026-11-23", "Día de la Soberanía Nacional"),

    # Feriados con Fines Turísticos (Puentes nacionales)
    ("2026-03-23", "Feriado con Fines Turísticos"),
    ("2026-07-10", "Feriado con Fines Turísticos"),
    ("2026-12-07", "Feriado con Fines Turísticos"),

    # Provinciales de San Luis
    ("2026-05-03", "Festividad del Santo Cristo de la Quebrada (San Luis)"),
    ("2026-05-04", "Festividad del Divino Señor de Renca (San Luis)"),
    ("2026-08-25", "Día de San Luis (Patrono de la Provincia)")
]

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró la base de datos en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Primero vemos cuántos feriados hay
    cursor.execute("SELECT COUNT(*) FROM feriados")
    inicial = cursor.fetchone()[0]
    print(f"Cantidad inicial de feriados en la DB: {inicial}")

    # Insertamos / reemplazamos los feriados de 2026
    agregados = 0
    for fecha, desc in FERIADOS_2026:
        cursor.execute("INSERT OR REPLACE INTO feriados (fecha, descripcion) VALUES (?, ?)", (fecha, desc))
        agregados += 1

    conn.commit()

    # Verificamos la cantidad final
    cursor.execute("SELECT COUNT(*) FROM feriados")
    final = cursor.fetchone()[0]
    print(f"Cantidad final de feriados en la DB: {final}")
    print(f"Se procesaron {agregados} feriados para el año 2026.")
    
    # Listamos todos los feriados de 2026 en la DB
    print("\nFeriados de 2026 actualmente registrados:")
    cursor.execute("SELECT fecha, descripcion FROM feriados WHERE fecha LIKE '2026-%' ORDER BY fecha")
    for row in cursor.fetchall():
        print(f" - {row[0]}: {row[1]}")
        
    conn.close()

if __name__ == "__main__":
    main()
