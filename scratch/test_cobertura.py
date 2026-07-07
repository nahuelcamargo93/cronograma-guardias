import main
from database import queries as q
from database.data_loader import obtener_empleados
from datetime import date, timedelta
from utils import time_to_float

servicio_id = 2
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

print("Cargando datos...")
empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
config_turnos, turnos_dict, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id, fecha_inicio, None)
feriados_indices = set()
offset_dia = date.fromisoformat(fecha_inicio).weekday()

print(f"Total empleados: {len(empleados)}")
print(f"Total turnos_dict: {list(turnos_dict.keys())}")

# Replicar lógica de candidatos de ventana de cobertura_dinamica.py
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
for dia in range(dias_del_bloque):
    es_f = ((dia + offset_dia) % 7) >= 5
    tipo_dia = "Finde_Feriado" if es_f else "Semana"
    fecha_actual_iso = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
    dia_semana_actual = (dia + offset_dia) % 7

    # Agrupar demandas
    candidates_by_window = {}
    for demanda in demanda_req.get(tipo_dia, []):
        dias_sem = demanda.get("dias_semana")
        applies = False
        if dias_sem:
            dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
            if dia_semana_actual in dias_validos:
                applies = True
        else:
            if tipo_dia == "Semana" and dia_semana_actual in [0, 1, 2, 3, 4]:
                applies = True
            elif tipo_dia == "Finde_Feriado" and dia_semana_actual in [5, 6]:
                applies = True

        if applies:
            puesto_key = demanda.get("puesto_id")
            key = (puesto_key, demanda["hora_inicio"], demanda["hora_fin"])
            candidates_by_window.setdefault(key, []).append(demanda)

    final_demandas = []
    for key, candidates in candidates_by_window.items():
        especificas = [c for c in candidates if c.get("dias_semana")]
        if especificas:
            final_demandas.extend(especificas)
        else:
            final_demandas.extend(candidates)

    demandas_por_ventana = {}
    for demanda in final_demandas:
        key = (demanda["hora_inicio"], demanda["hora_fin"])
        demandas_por_ventana.setdefault(key, []).append(demanda)

    for (h_start, h_end), window_demands in demandas_por_ventana.items():
        d_h_start = time_to_float(h_start)
        d_h_end = time_to_float(h_end)
        d_abs_start = dia * 24 + d_h_start
        if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
            d_abs_end = (dia + 1) * 24 + d_h_end
        elif d_h_end == 0 and d_h_start > 0:
            d_abs_end = (dia + 1) * 24
        else:
            d_abs_end = dia * 24 + d_h_end

        for dem in window_demands:
            p_min = dem.get("cantidad_min")
            p_puesto = dem.get("puesto")
            
            # Ver cuántos empleados pueden cubrir esta ventana hoy (sin licencias)
            pool_count = 0
            for emp in empleados:
                # Ver si se crearía la variable para este empleado y día
                # Replicamos filtro de main.py para creación de variable
                for t_nombre, t_info in turnos_dict.items():
                    if t_info.get('solo_importacion', 0):
                        continue
                    if t_info.get('puesto_nombre') != dem["puesto"]:
                        continue
                        
                    # Días habilitados
                    dias_hab_str = t_info.get("dias_semana", "0,1,2,3,4,5,6")
                    dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
                    if es_f:
                        if not (5 in dias_permitidos or 6 in dias_permitidos):
                            continue
                    else:
                        if dia_semana_actual not in dias_permitidos:
                            continue
                            
                    # Exclusión de puesto
                    if emp.puestos_habilitados:
                        if dem["puesto"] not in emp.puestos_habilitados:
                            continue
                    
                    # Ver si calza con la ventana
                    ts_abs = dia * 24 + time_to_float(t_info['hora_inicio'])
                    te_abs = ts_abs + t_info['horas']
                    if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                        pool_count += 1
            
            if pool_count < p_min:
                print(f"!!! CONFLICTO DETECTADO el dia {dia} ({fecha_actual_iso}, {tipo_dia}): Ventana {h_start}-{h_end} para puesto {p_puesto} requiere min {p_min}, pero solo hay {pool_count} variables que la cubren.")
            else:
                pass

print("Verificación de cobertura finalizada.")
