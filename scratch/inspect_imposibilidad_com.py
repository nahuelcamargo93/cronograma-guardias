import sys
import os
sys.path.append(os.path.abspath("."))
import sqlite3
from datetime import datetime, date, timedelta
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import FECHA_INICIO, FECHA_FIN, FERIADOS

print("FECHA_INICIO:", FECHA_INICIO)
print("FECHA_FIN:", FECHA_FIN)

conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

# Let's inspect DEMANDA CONFIG
print("\n--- DEMANDA CONFIG active for COM (servicio 4) ---")
cur = conn.execute("""
    SELECT dc.*, p.nombre as puesto_nombre
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 4 AND dc.activo = 1
""")
dem_configs = [dict(r) for r in cur]

# Load staff
fecha_inicio_dt = datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
fecha_fin_dt = datetime.strptime(FECHA_FIN, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

empleados = obtener_empleados(4, FECHA_INICIO, total_dias)
print(f"\nTotal staff loaded: {len(empleados)}")

feriados_indices = []
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

print("\n--- DAY-BY-DAY AVAILABILITY VS DEMAND (CORRECTED) ---")
# Let's check day by day
for d in range(total_dias):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    fecha_str = fecha_d.strftime("%Y-%m-%d")
    es_finde = ((d + offset_dia) % 7) >= 5 or d in feriados_indices
    tipo_dia = "Finde_Feriado" if es_finde else "Semana"
    weekday = (d + offset_dia) % 7
    
    # Calculate demand for Monitoristas
    # Find active demands for this day for Monitorista (puesto_id = 32)
    dem_puesto_32 = []
    for dc in dem_configs:
        if dc["puesto_id"] == 32 and dc["tipo_dia"] == tipo_dia:
            # Check if it applies to this day
            d_sem = dc.get("dias_semana")
            if d_sem:
                d_list = [int(x.strip()) for x in d_sem.split(",") if x.strip().isdigit()]
                if weekday in d_list:
                    dem_puesto_32.append(dc)
            else:
                if d in feriados_indices:
                    dem_puesto_32.append(dc)
                elif tipo_dia == "Semana" and weekday in [0, 1, 2, 3, 4]:
                    dem_puesto_32.append(dc)
                elif tipo_dia == "Finde_Feriado" and weekday in [5, 6]:
                    dem_puesto_32.append(dc)
                    
    # Filter specific vs generic
    # If there are specific ones (with dias_semana), remove the ones without
    has_specific = any(x.get("dias_semana") is not None for x in dem_puesto_32)
    if has_specific:
        dem_puesto_32 = [x for x in dem_puesto_32 if x.get("dias_semana") is not None]
        
    tot_min_demand = sum(x["cantidad_min"] for x in dem_puesto_32)
    
    # Count available monitoristas
    avail_count = 0
    avail_names = []
    for emp in empleados:
        if emp.rol != "Monitorista" and emp.rol != "Supervisor Suplente":
            continue
        if d in emp.dias_licencia:
            continue
        avail_count += 1
        avail_names.append(emp.nombre)
        
    if tot_min_demand > avail_count:
        print(f"CRITICAL: {fecha_str} (WD {weekday}) | Demand Min: {tot_min_demand} | Available: {avail_count} ({', '.join(avail_names)})")
    else:
        print(f"OK: {fecha_str} (WD {weekday}) | Demand Min: {tot_min_demand} | Available: {avail_count}")

conn.close()
