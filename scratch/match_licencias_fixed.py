import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("\n--- All Personnel with Service ---")
df_personal_all = pd.read_sql_query("""
    SELECT p.nombre, s.nombre as servicio
    FROM personal p
    JOIN servicios s ON p.servicio_id = s.id
""", conn)
print(df_personal_all.head())

print("\n--- All Licencias ---")
df_licencias = pd.read_sql_query("SELECT * FROM licencias", conn)
print(df_licencias.head())

# Matching
results = []
for idx, row in df_licencias.iterrows():
    lic_name = row['nombre'].upper().strip()
    found = False
    for p_idx, p_row in df_personal_all.iterrows():
        p_name = p_row['nombre'].upper().strip()
        # Try different matching strategies
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

print("\n--- License Count by Service ---")
summary = df_results.groupby('servicio').size()
print(summary)

print("\n--- Detailed Results ---")
print(df_results)

conn.close()
