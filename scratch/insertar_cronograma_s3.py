import sqlite3
from datetime import datetime

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Definir los nombres exactos y sus roles
# Usamos búsquedas robustas en la base de datos para no errar con acentos o caracteres especiales.
name_patterns = {
    "Arias": "Arias, Guillermina",
    "Baracat": "Baracat, Denisse",
    "Mora": "Mora, Sergio Enrique",
    "Noriega": "Noriega, Claudio Martín",
    "Zeballos": "Zeballos, Valeria Alejandra",
    "Pacheco": "Pacheco, Celeste",
    "Diaz": "Diaz Villafañe Morales, Abigail",
    "Nesteruk": "Nesteruk, María Silvia",
    "Quiroga": "Quiroga Sassu, Maria Macarena",
    "Sánchez": "Sánchez Reinoso, Ana Belén",
    "Villegas": "Villegas Oliva, Maria Belén"
}

resolved_names = {}
for short_name, fallback_full in name_patterns.items():
    # Buscar en la base de datos
    cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE ? AND servicio_id = 3;", (f"%{short_name}%",))
    res = cursor.fetchone()
    if res:
        resolved_names[short_name] = res[0]
        print(f"Resolución de nombre: '{short_name}' -> '{res[0]}'")
    else:
        # Intentar sin acento o con comodín para la última vocal/caracter especial si es Sánchez
        clean_search = short_name.replace("á", "_").replace("é", "_").replace("í", "_").replace("ó", "_").replace("ú", "_").replace("ñ", "_")
        cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE ? AND servicio_id = 3;", (f"%{clean_search}%",))
        res = cursor.fetchone()
        if res:
            resolved_names[short_name] = res[0]
            print(f"Resolución de nombre (búsqueda relajada): '{short_name}' -> '{res[0]}'")
        else:
            resolved_names[short_name] = fallback_full
            print(f"ADVERTENCIA: No se encontró '{short_name}' en la BD. Usando fallback: '{fallback_full}'")

# Guardias a insertar
guardias_data = [
    # 29/6
    {"fecha": "2026-06-29", "short_name": "Arias", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-29", "short_name": "Baracat", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-29", "short_name": "Mora", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-29", "short_name": "Noriega", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-29", "short_name": "Zeballos", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-29", "short_name": "Pacheco", "turno": "G_Residente", "horas": 24, "es_finde": 0},
    
    # 30/6
    {"fecha": "2026-06-30", "short_name": "Diaz", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-30", "short_name": "Nesteruk", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-30", "short_name": "Quiroga", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-30", "short_name": "Sánchez", "turno": "G_Planta", "horas": 24, "es_finde": 0},
    {"fecha": "2026-06-30", "short_name": "Villegas", "turno": "G_Residente", "horas": 24, "es_finde": 0},
]

try:
    # 2. Insertar cabecera de cronograma
    # Nota: Rango todo Junio (2026-06-01 a 2026-06-30) con estado 'aprobado'
    creado_en = datetime.now().isoformat(timespec='seconds')
    cursor.execute("""
        INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas, estado)
        VALUES ('2026-06-01', '2026-06-30', ?, 'Cronograma aprobado Junio 29-30 (24hs)', 'aprobado');
    """, (creado_en,))
    
    cronograma_id = cursor.lastrowid
    print(f"\n[OK] Insertado cronograma id={cronograma_id} para Junio 2026 con estado aprobado")

    # 3. Insertar las guardias individuales
    inserted_count = 0
    for g in guardias_data:
        full_name = resolved_names[g["short_name"]]
        cursor.execute("""
            INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde, servicio_id)
            VALUES (?, ?, ?, ?, ?, ?, 3);
        """, (cronograma_id, full_name, g["fecha"], g["turno"], g["horas"], g["es_finde"]))
        inserted_count += 1
        print(f"  Insertada guardia: {full_name} ({g['fecha']} - {g['turno']} - {g['horas']} hs)")

    conn.commit()
    print(f"\n[OK] Transacción exitosa. Se insertaron {inserted_count} guardias.")

except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Ocurrió un error y se revirtió la transacción: {e}")
finally:
    conn.close()
