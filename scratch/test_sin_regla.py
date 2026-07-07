import sqlite3
import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import ejecutar_optimizacion

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
# Desactivar la regla
conn.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 2 AND codigo_regla = 'TURNO_PREVIO_LICENCIA'")
conn.commit()
conn.close()

print("Regla TURNO_PREVIO_LICENCIA desactivada. Corriendo optimización normal...")
res = ejecutar_optimizacion(servicio_id=2, fecha_inicio="2026-08-01", fecha_fin="2026-08-31", modo_debug=False, max_time_in_seconds=30)
print("Resultado:", res)

# Restaurar la regla
conn = sqlite3.connect(db_path)
conn.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 2 AND codigo_regla = 'TURNO_PREVIO_LICENCIA'")
conn.commit()
conn.close()
print("Regla restaurada.")
