import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("\n--- Sample of 'personal' table ---")
df_personal = pd.read_sql_query("""
    SELECT p.id, p.nombre, s.nombre as servicio
    FROM personal p
    JOIN servicios s ON p.servicio_id = s.id
    LIMIT 10
""", conn)
print(df_personal)

print("\n--- All Licencias with Service Name ---")
# Since names might not match exactly, I'll try to find if the license name is contained in the personal name or vice versa
# Or check if there's a more direct way.
# Let's try to join on names, but maybe normalizing them.

df_licencias = pd.read_sql_query("SELECT * FROM licencias", conn)
df_personal_all = pd.read_sql_query("""
    SELECT p.nombre, s.nombre as servicio
    FROM personal p
    JOIN servicios s ON p.servicio_id = s.id
""", conn)

# Simple check: how many licenses per service?
results = []
for idx, row in df_licencias.iterrows():
    lic_name = row['nombre'].upper()
    found = False
    for p_idx, p_row in df_personal_all.iterrows():
        p_name = p_row['nombre'].upper()
        if lic_name in p_name or p_name in lic_name:
            results.append({
                'lic_name': row['nombre'],
                'personal_name': p_row['nombre'],
                'servicio': p_row['servicio'],
                'tipo': row['tipo'],
                'inicio': row['fecha_inicio'],
                'fin': row['fecha_fin']
            })
            found = True
            break
    if not found:
        results.append({
            'lic_name': row['nombre'],
            'personal_name': 'NOT FOUND',
            'servicio': 'UNKNOWN',
            'tipo': row['tipo'],
            'inicio': row['fecha_inicio'],
            'fin': row['fecha_fin']
        })

df_results = pd.DataFrame(results)
print(df_results)

print("\n--- License Count by Service ---")
print(df_results.groupby('servicio').size())

conn.close()
