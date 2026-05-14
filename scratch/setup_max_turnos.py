"""
Configura la regla MAX_TURNOS en la base de datos:
1. Agrega MAX_TURNOS al catalogo de reglas
2. Configura la regla de servicio: max 2 noches por semana
3. Suspende la regla para Juarez indefinidamente (hasta 2031)
"""
import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

# 1. Registrar en el catálogo
conn.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES (
        'MAX_TURNOS',
        'HARD',
        'Limite maximo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Noche", "max_por_semana": 2}]'
    )
""")

# 2. Obtener ID de la regla y del servicio
regla_id = conn.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MAX_TURNOS'").fetchone()[0]
print(f"ID regla MAX_TURNOS: {regla_id}")

# 3. Configurar en servicios_reglas: max 2 noches por semana para el servicio 1
params_servicio = json.dumps([{"turno": "Noche", "max_por_semana": 2}])
conn.execute("""
    INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json)
    VALUES (1, ?, ?)
    ON CONFLICT(servicio_id, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
""", (regla_id, params_servicio))
print(f"Regla de servicio configurada: {params_servicio}")

# 4. Suspender la regla para Juarez hasta 2031 (indefinidamente)
conn.execute("""
    INSERT INTO personal_reglas_ajustes 
        (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
    VALUES ('Lic. Juarez', 'MAX_TURNOS', '2026-01-01', '2031-12-31', 'SUSPENDER', NULL, 1)
""")
print("Suspension de MAX_TURNOS para Lic. Juarez configurada (2026-2031)")

conn.commit()
conn.close()
print("\nDB actualizada correctamente.")
