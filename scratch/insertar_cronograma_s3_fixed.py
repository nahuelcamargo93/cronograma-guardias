import sqlite3
from datetime import datetime

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # 1. Eliminar el cronograma erróneo (id=491)
    print("Eliminando cronograma id=491 y sus guardias...")
    cursor.execute("DELETE FROM cronogramas WHERE id = 491;")
    print("Eliminado con éxito.")
    
    # 2. Definir los patrones de búsqueda exactos por prefijo de apellido
    surname_patterns = {
        "Arias": "Arias,%",
        "Baracat": "Baracat,%",
        "Mora": "Mora,%",
        "Noriega": "Noriega,%",
        "Zeballos": "Zeballos,%",
        "Pacheco": "Pacheco,%",
        "Diaz": "Diaz%",  # sin coma por si acaso
        "Nesteruk": "Nesteruk,%",
        "Quiroga": "Quiroga%",
        "Sánchez": "S%nchez%", # para evitar problemas de acento / encoding
        "Villegas": "Villegas%"
    }

    resolved_names = {}
    for short_name, pattern in surname_patterns.items():
        cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE ? AND servicio_id = 3 AND COALESCE(activo, 1) = 1;", (pattern,))
        rows = cursor.fetchall()
        if len(rows) == 1:
            resolved_names[short_name] = rows[0][0]
            print(f"Resolución unívoca: '{short_name}' -> '{rows[0][0]}'")
        elif len(rows) > 1:
            # Si hay más de uno, elegir el que coincida mejor o levantar excepción
            print(f"Múltiples resultados para '{short_name}' con patrón '{pattern}':")
            for r in rows:
                print(f"  - {r[0]}")
            # Filtrar el que empieza exactamente con short_name
            exact_match = [r[0] for r in rows if r[0].startswith(short_name + ",")]
            if len(exact_match) == 1:
                resolved_names[short_name] = exact_match[0]
                print(f"  -> Seleccionado por coincidencia exacta de prefijo: '{exact_match[0]}'")
            else:
                raise ValueError(f"Conflicto de nombres múltiples para '{short_name}'")
        else:
            raise ValueError(f"No se encontró ningún personal para '{short_name}' con patrón '{pattern}'")

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

    # 3. Insertar cabecera de cronograma
    creado_en = datetime.now().isoformat(timespec='seconds')
    cursor.execute("""
        INSERT INTO cronogramas (fecha_inicio, fecha_fin, creado_en, notas, estado)
        VALUES ('2026-06-01', '2026-06-30', ?, 'Cronograma aprobado Junio 29-30 (24hs)', 'aprobado');
    """, (creado_en,))
    
    cronograma_id = cursor.lastrowid
    print(f"\n[OK] Insertado cronograma id={cronograma_id} para Junio 2026 con estado aprobado")

    # 4. Insertar las guardias individuales
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
