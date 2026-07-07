import sys, os
sys.path.append(os.getcwd())
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# 1. Eliminar asignación fija de fecha id=103
cursor.execute("DELETE FROM personal_asignaciones_fijas WHERE id = 103")
print(f"Eliminadas {cursor.rowcount} asignaciones fijas con id = 103.")

# 2. Eliminar franco forzado duplicado id=1854
cursor.execute("DELETE FROM personal_reglas_ajustes WHERE id = 1854")
print(f"Eliminados {cursor.rowcount} ajustes de regla con id = 1854.")

conn.commit()
conn.close()
print("Limpieza completada con éxito.")
