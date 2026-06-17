import os
import sys
import calendar
from datetime import date, timedelta

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from restricciones.hard._utils import is_finde
import rule_engine as _re

def main():
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    # Cargar datos base
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = {'__servicio__': []}
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
    turnos_dict = obtener_turnos(servicio_id)
    
    # Feriados y offset
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    offset_dia = fecha_inicio_dt.weekday()
    
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < 31:
            feriados_indices.append(delta)
    feriados_set = set(feriados_indices)

    # Re-crear variables turnos de la misma forma que main.py
    turnos = {}
    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        for dia in range(31):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_set)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            
            for t in lista_turnos:
                t_config = config_turnos.get(tipo_dia, {}).get(t, {})
                dias_hab_str = t_config.get("Dias_Habilitados", "0,1,2,3,4,5,6")
                dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
                
                if es_finde_o_feriado:
                    if not (5 in dias_permitidos or 6 in dias_permitidos):
                        continue
                else:
                    if dia_semana not in dias_permitidos:
                        continue

                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                
                if puesto_nombre_turno:
                    if emp.puestos_habilitados:
                        if puesto_nombre_turno not in emp.puestos_habilitados:
                            continue
                    else:
                        if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                            continue
                
                turnos[(nombre, dia, t)] = f"var_{nombre}_d{dia}_{t}"

    # Diagnosticar para ARCE DANIEL y PALANA GRACIELA
    for target_name in ["ARCE DANIEL", "PALANA GRACIELA"]:
        print(f"\n==========================================")
        print(f"DIAGNÓSTICO PARA: {target_name}")
        print(f"==========================================")
        
        emp = next((e for e in empleados if e.nombre == target_name), None)
        if not emp:
            print("Empleado no encontrado!")
            continue
            
        print(f"Puestos habilitados: {emp.puestos_habilitados}")
        print(f"Rol: {emp.rol}")
        print(f"Días de licencia: {emp.dias_licencia}")
        
        # Simular min_horas_mes_calendario.py
        meses = {}
        for d in range(31):
            meses.setdefault((fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m"), []).append(d)

        for m_key, dias_m in meses.items():
            ref = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            p_min = _re.resolver_parametros_regla(
                'MIN_HORAS_MES_CALENDARIO', emp.nombre, ref,
                reglas_servicio_db, emp.reglas, {}
            )
            p_max = _re.resolver_parametros_regla(
                'MAX_HORAS_MES_CALENDARIO', emp.nombre, ref,
                reglas_servicio_db, emp.reglas, {}
            )
            print(f"Parámetros MIN_HORAS_MES_CALENDARIO: {p_min}")
            print(f"Parámetros MAX_HORAS_MES_CALENDARIO: {p_max}")
            
            min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
            if p_max and not _re.regla_suspendida(p_max):
                max_h_ref = p_max.get('max_horas', 192) if isinstance(p_max, dict) else 192
                if min_h > max_h_ref:
                    min_h = max_h_ref
            
            vars_h = []
            max_horas_posibles = 0
            for d in dias_m:
                td = "Finde_Feriado" if is_finde(d, offset_dia, feriados_set) else "Semana"
                for t in config_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos:
                        vars_h.append((d, t, turnos_dict[t].horas))
                        # Si no estuviera de licencia, sumaría
                        if d not in emp.dias_licencia:
                            max_horas_posibles += turnos_dict[t].horas
            
            print(f"Cantidad de variables de turnos creadas en el mes: {len(vars_h)}")
            print(f"Máxima cantidad teórica de horas que podría hacer si trabajara todos los turnos disponibles (y sin licencias): {max_horas_posibles}")
            
            dias_lic = [d for d in dias_m if d in emp.dias_licencia]
            y, m = map(int, m_key.split("-"))
            dias_del_mes = calendar.monthrange(y, m)[1]
            
            horas_lic = int((float(min_h) / dias_del_mes) * len(dias_lic) + 0.5)
            piso = int((float(min_h) / dias_del_mes) * len(dias_m) + 0.5)
            
            print(f"Días del mes (dias_del_mes): {dias_del_mes}")
            print(f"Días planificados (len(dias_m)): {len(dias_m)}")
            print(f"Días de licencia en el mes (len(dias_lic)): {len(dias_lic)}")
            print(f"Piso calculado (piso): {piso}")
            print(f"Crédito por licencia (horas_lic): {horas_lic}")
            print(f"Piso Neto Requerido (piso - horas_lic): {piso - horas_lic}")
            
            # Ver qué turnos tiene disponibles cada día
            print("\nDistribución de variables disponibles por día:")
            for d in dias_m:
                ts_disponibles = [t for (emp_n, dia_n, t) in turnos if emp_n == emp.nombre and dia_n == d]
                print(f"  Día {d} ({'Finde' if is_finde(d, offset_dia, feriados_set) else 'Semana'}): {ts_disponibles}")

if __name__ == "__main__":
    main()
