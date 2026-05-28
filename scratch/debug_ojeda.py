import sys
sys.path.insert(0, '.')
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor()

# Check turno names for Administrativo
print('=== TURNOS ADMINISTRATIVO (turnos_config) ===')
cur.execute("""
    SELECT tc.nombre, tc.hora_inicio, tc.horas, p.nombre as puesto, tc.servicio_id
    FROM turnos_config tc
    JOIN puestos p ON tc.puesto_id = p.id 
    WHERE p.nombre LIKE '%dministrat%' OR tc.nombre LIKE '%dministrat%'
""")
print(cur.fetchall())

# Check feriados equidad rules for service 4
print()
print('=== REGLAS SERVICIO 4 (servicios_reglas) ===')
cur.execute("""
    SELECT codigo_regla, parametros_json
    FROM servicios_reglas
    WHERE servicio_id = 4 AND codigo_regla IN ('PESO_EQUIDAD_FERIADOS', 'PESO_EQUIDAD_FINDES_MENSUAL', 'LIMITES_SOFT_RULES')
""")
for row in cur.fetchall():
    print(row)

# How does df_personal look - check what queries.py returns
print()
print('=== CHECKING get_personal_servicio(4) ===')
import database.queries as dq
df_p = dq.get_personal_servicio(4)
print("Columns:", df_p.columns.tolist())
ojeda = df_p[df_p['nombre'].str.contains('OJEDA', case=False, na=False)]
print("Ojeda row:")
for col in df_p.columns:
    val = ojeda.iloc[0][col] if len(ojeda) > 0 else 'N/A'
    print(f"  {col}: {val}")

print()
briz = df_p[df_p['nombre'].str.contains('BRIZUELA', case=False, na=False)]
print("Brizuela rows:")
for _, row in briz.iterrows():
    print(f"  nombre={row['nombre']}, categoria={row.get('categoria','?')}, rol={row.get('rol','?')}")

conn.close()
