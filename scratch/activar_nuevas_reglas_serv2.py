import sqlite3
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Asegurar reglas en catálogo
reglas_nuevas = [
    ('NO_REPETIR_TURNO_CONSECUTIVO', 'HARD', 'Prohíbe repetir el mismo tipo de turno semanal en semanas consecutivas'),
    ('ORDEN_ROTACION_SEMANAL', 'SOFT', 'Penaliza desvíos en el orden ideal de rotación de turnos semanal (M -> T -> TN -> N)')
]

for codigo, tipo, desc in reglas_nuevas:
    cursor.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES (?, ?, ?)
        ON CONFLICT(codigo_regla) DO UPDATE SET tipo = excluded.tipo, descripcion = excluded.descripcion
    """, (codigo, tipo, desc))

# 2. Activar para servicio_id = 2
# NO_REPETIR_TURNO_CONSECUTIVO (HARD)
cursor.execute("""
    INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
    VALUES (2, 'NO_REPETIR_TURNO_CONSECUTIVO', '{}', 1)
    ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo = 1, parametros_json = '{}'
""")

# ORDEN_ROTACION_SEMANAL (SOFT, peso = 1000)
cursor.execute("""
    INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
    VALUES (2, 'ORDEN_ROTACION_SEMANAL', '{"peso": 1000}', 1)
    ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo = 1, parametros_json = '{"peso": 1000}'
""")

conn.commit()

# Verificación
print("--- Reglas en catálogo ---")
cursor.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla IN ('NO_REPETIR_TURNO_CONSECUTIVO', 'ORDEN_ROTACION_SEMANAL')")
for row in cursor.fetchall():
    print(row)

print("\n--- Reglas de Servicio 2 ---")
cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla IN ('NO_REPETIR_TURNO_CONSECUTIVO', 'ORDEN_ROTACION_SEMANAL')")
for row in cursor.fetchall():
    print(row)

conn.close()
