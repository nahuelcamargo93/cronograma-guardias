import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Total de médicos de planta activos
cursor.execute("SELECT COUNT(*), GROUP_CONCAT(nombre) FROM personal WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1")
count_med, names_med = cursor.fetchone()
print(f"Total médicos activos en servicio 3: {count_med}")

# 2. Cargar la demanda base
cursor.execute("""
    SELECT dc.tipo_dia, p.nombre, dc.cantidad_min, dc.cantidad_max, dc.hora_inicio, dc.hora_fin 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3 AND dc.activo = 1
""")
demanda = cursor.fetchall()
print("\nDemanda configurada:")
for d in demanda:
    print(d)

# 3. Calcular total de horas demandadas en Julio 2026
import datetime
start_date = datetime.date(2026, 7, 1)
end_date = datetime.date(2026, 7, 31)

# Obtener feriados
cursor.execute("SELECT fecha FROM feriados WHERE fecha BETWEEN '2026-07-01' AND '2026-07-31'")
feriados = {r[0] for r in cursor.fetchall()}

dias_semana = 0
dias_finde = 0
curr = start_date
while curr <= end_date:
    fecha_str = curr.isoformat()
    if curr.weekday() >= 5 or fecha_str in feriados:
        dias_finde += 1
    else:
        dias_semana += 1
    curr += datetime.timedelta(days=1)

print(f"\nJulio 2026 tiene {dias_semana} días de semana y {dias_finde} días de fin de semana/feriado.")

# Calcular horas demandadas base
# Para cada demanda, calculamos la duración en horas y multiplicamos por la cantidad y la cantidad de días de ese tipo
demanda_total_horas = 0
for tipo_dia, puesto, cant_min, cant_max, h_ini, h_fin in demanda:
    # Duración del puesto.
    # En médicos, los puestos son G_Planta (24h), D_Planta (12h), N_Planta (12h), etc.
    # Miremos si podemos deducir las horas desde turnos_config de ese puesto.
    cursor.execute("SELECT horas FROM turnos_config WHERE puesto_id = (SELECT id FROM puestos WHERE nombre = ? AND servicio_id = 3)", (puesto,))
    row_t = cursor.fetchone()
    horas_puesto = row_t[0] if row_t else 24
    
    cant_dias = dias_finde if tipo_dia == 'Finde_Feriado' else dias_semana
    horas_totales = cant_dias * cant_min * horas_puesto
    demanda_total_horas += horas_totales
    print(f"  Puesto {puesto} ({tipo_dia}): {cant_min} vacantes * {horas_puesto} horas * {cant_dias} días = {horas_totales} horas")

print(f"Demanda total de horas base: {demanda_total_horas}")

# 4. Chequear si hay reglas de mínimos y máximos de horas específicas
print("\n--- Reglas de horas de personal ---")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json 
    FROM personal_reglas 
    WHERE codigo_regla IN ('MIN_HORAS_MES_CALENDARIO', 'MAX_HORAS_MES_CALENDARIO') AND activo = 1
      AND personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Ajustes de horas de personal en Julio 2026 ---")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla IN ('MIN_HORAS_MES_CALENDARIO', 'MAX_HORAS_MES_CALENDARIO') AND activo = 1
      AND personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
      AND fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01'
""")
for r in cursor.fetchall():
    print(r)

conn.close()
