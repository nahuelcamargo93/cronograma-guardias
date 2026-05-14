import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Registrar la nueva regla en el catálogo
cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, descripcion, tipo) VALUES (?, ?, ?)", 
               ('PENALIZACION_TURNO', 'Penaliza la asignación de un turno específico', 'SOFT'))

# Obtener IDs
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PENALIZACION_TURNO'")
regla_id = cursor.fetchone()[0]

cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PESO_TURNOS_LARGOS'")
row_old = cursor.fetchone()
old_regla_id = row_old[0] if row_old else None

# 2. Configurar en el Servicio 2 (Enfermería)
# Usaremos una lista de dicts para permitir múltiples turnos penalizados
parametros = [
    {"turno": "MT", "peso": 500},
    {"turno": "TNN", "peso": 500}
]

# Insertar o actualizar
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", (regla_id,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
               (2, regla_id, json.dumps(parametros)))

# Suspendemos la anterior si existía para evitar duplicidad
if old_regla_id:
    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?",
                   (json.dumps({"suspendida": True, "peso": 0}), old_regla_id))

conn.commit()
print("Regla PENALIZACION_TURNO configurada en DB para Servicio 2 (MT y TNN con peso 500)")
conn.close()
