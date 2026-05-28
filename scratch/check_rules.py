import sys; sys.path.insert(0,'.')
from database.connection import get_connection
conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre LIKE '%OJEDA%' AND codigo_regla='EXCLUIR_TURNOS'")
print('OJEDA actual:', cur.fetchone())

cur.execute("SELECT personal_nombre, codigo_regla, parametros_json FROM personal_reglas WHERE personal_nombre LIKE '%BRIZUELA%'")
print('BRIZUELA reglas:', cur.fetchall())

# Check all service 4 rules
cur.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 4")
print()
print('=== ALL SERVICE 4 RULES ===')
for row in cur.fetchall():
    print(row)

conn.close()
