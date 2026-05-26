import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

# Check matching demanda_config for 2026-06-10
d = 9 # June 10 is the 10th day (index 9 from June 1)
weekday = 2 # Wednesday
tipo_dia = "Semana"

print("--- MATCHING DEMANDA CONFIGS FOR WEDNESDAY JUNE 10 ---")
cur = conn.execute("""
    SELECT dc.*, p.nombre as puesto_nombre
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 4 AND dc.activo = 1
""")
dem_configs = [dict(r) for r in cur]

matching = []
for dc in dem_configs:
    d_sem = dc.get("dias_semana")
    if d_sem:
        d_list = [int(x.strip()) for x in d_sem.split(",") if x.strip().isdigit()]
        if weekday in d_list:
            matching.append(dc)
    else:
        if tipo_dia == "Semana" and weekday in [0, 1, 2, 3, 4]:
            matching.append(dc)

for m in matching:
    print(m)

conn.close()
