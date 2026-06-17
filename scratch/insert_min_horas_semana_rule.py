import sqlite3
import json

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
try:
    # 1. Insertar en reglas_catalogo
    conn.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('MIN_HORAS_SEMANA', 'HARD', 'Piso mínimo de horas trabajadas por semana')
    """)
    # 2. Insertar en servicios_reglas para servicio_id = 1
    conn.execute("""
        DELETE FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'MIN_HORAS_SEMANA'
    """)
    conn.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (1, 'MIN_HORAS_SEMANA', ?, 1)
    """, (json.dumps({"min_horas": 18, "modo": "HARD"}),))
    conn.commit()
    print("¡Regla MIN_HORAS_SEMANA insertada con éxito para el servicio ID 1 en la BD!")
finally:
    conn.close()
