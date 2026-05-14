import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Registrar la nueva regla en el catálogo
cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, descripcion, tipo) VALUES (?, ?, ?)", 
               ('BONUS_POR_CARGA_PERFECTA', 'Premio por carga horaria mensual perfecta (entre 142 y 146 horas)', 'SOFT'))

# Obtener ID
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'BONUS_POR_CARGA_PERFECTA'")
regla_id = cursor.fetchone()[0]

# 2. Configurar en el Servicio 2 (Enfermería)
parametros = {
    "min_h": 142,
    "max_h": 146,
    "bonus": 3000
}

# Insertar o actualizar
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", (regla_id,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
               (2, regla_id, json.dumps(parametros)))

conn.commit()
print("Regla BONUS_POR_CARGA_PERFECTA configurada en DB para Servicio 2 (142-146hs, Premio: 3000)")
conn.close()
