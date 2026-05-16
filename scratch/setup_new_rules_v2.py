import sqlite3
import os
import json

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Registrar nuevas reglas en el catalogo
nuevas_reglas = [
    ('MIN_FINDES_MES', 'Asegura que el personal tenga al menos N fines de semana trabajados en el mes.', 'HARD'),
    ('PERSONAL_EXTRA_FUERA_MINIMO', 'El personal indicado no cuenta para el cupo minimo pero si ocupa lugar en el maximo.', 'HARD')
]

for codigo, desc, tipo in nuevas_reglas:
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (codigo,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO reglas_catalogo (codigo_regla, descripcion, tipo) VALUES (?, ?, ?)", (codigo, desc, tipo))

# 2. Activar reglas para Servicio 3 (Medicos)
# Minimo 1 finde para todos
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_FINDES_MES'")
rule_id_min_f = cursor.fetchone()[0]
params_min_f = json.dumps({"min_findes": 1})
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = ?", (rule_id_min_f,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, ?)", (rule_id_min_f, params_min_f))

# Personal Extra (Baracat Denisse)
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PERSONAL_EXTRA_FUERA_MINIMO'")
rule_id_extra = cursor.fetchone()[0]
params_extra = json.dumps({"nombres": ["Baracat Denisse"]})
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = ?", (rule_id_extra,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, ?)", (rule_id_extra, params_extra))

# 3. Ajustar Penalizaciones (N > D)
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PENALIZACION_TURNO'")
rule_id_penal = cursor.fetchone()[0]
params_penal = json.dumps([
    {"turno": "D_Planta", "peso": 2000}, 
    {"turno": "N_Planta", "peso": 4000},
    {"turno": "D_Residente", "peso": 2000},
    {"turno": "N_Residente", "peso": 4000}
])
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = ?", (rule_id_penal,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, ?)", (rule_id_penal, params_penal))

conn.commit()
print("Base de datos actualizada con las nuevas reglas y penalizaciones.")
conn.close()
