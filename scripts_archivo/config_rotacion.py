import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Registrar la nueva regla en el catálogo
cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, descripcion, tipo) VALUES (?, ?, ?)", 
               ('OBJETIVO_ROTACION_MENSUAL', 'Penaliza desviaciones del objetivo ideal de semanas por turno (ej. 1 de cada uno)', 'SOFT'))

# Obtener ID
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'OBJETIVO_ROTACION_MENSUAL'")
regla_id = cursor.fetchone()[0]

# 2. Configurar en el Servicio 2 (Enfermería)
# Objetivo: 1 semana de cada uno, con un peso de 200 por cada semana de desvío
parametros = {
    "objetivos": {"M": 1, "T": 1, "TN": 1, "N": 1},
    "peso": 200
}

# Insertar o actualizar
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", (regla_id,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
               (2, regla_id, json.dumps(parametros)))

conn.commit()
print("Regla OBJETIVO_ROTACION_MENSUAL configurada en DB para Servicio 2 (Target: 1-1-1-1, Peso: 200)")
conn.close()
