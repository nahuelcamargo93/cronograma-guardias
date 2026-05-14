import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Registrar la nueva regla en el catálogo
cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, descripcion, tipo) VALUES (?, ?, ?)", 
               ('PENALIZACION_TURNO_AUSENTE', 'Penaliza si una persona no tiene al menos una semana de un tipo específico en el mes', 'SOFT'))

# Obtener ID
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PENALIZACION_TURNO_AUSENTE'")
regla_id = cursor.fetchone()[0]

# 2. Configurar en el Servicio 2 (Enfermería)
parametros = {
    "peso": 1500 # Peso alto para forzar diversidad
}

# Insertar o actualizar
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", (regla_id,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
               (2, regla_id, json.dumps(parametros)))

conn.commit()
print("Regla PENALIZACION_TURNO_AUSENTE configurada en DB para Servicio 2 (Peso: 1500)")
conn.close()
