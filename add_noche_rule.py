import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cronograma_inteligente.db")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES ('MAX_NOCHE_VS_DIA', 'HARD', 'El total de personal en turnos de noche no puede superar al total en turnos de día.')")
c.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MAX_NOCHE_VS_DIA'")
regla_id = c.fetchone()[0]

# Aplicar solo para el servicio 3 (Médicos)
c.execute("INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, '{}')", (regla_id,))

conn.commit()
print("Regla añadida a DB y asignada al servicio 3!")
