import sys
import os
sys.path.append(os.path.abspath("."))

from datetime import date, timedelta
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

def debug():
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    
    # Obtener días del bloque (mes completo)
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    if fecha_inicio_dt.month == 12:
        siguiente_mes = fecha_inicio_dt.replace(year=fecha_inicio_dt.year + 1, month=1, day=1)
    else:
        siguiente_mes = fecha_inicio_dt.replace(month=fecha_inicio_dt.month + 1, day=1)
    fecha_fin_dt = siguiente_mes - timedelta(days=1)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    fecha_fin = fecha_fin_dt.isoformat()

    # 1. Cargar datos igual que en main.py
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    turnos_dict = obtener_turnos(servicio_id)
    
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    feriados_indices = []
    for f_str in feriados_db:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)
            
    offset_dia = fecha_inicio_dt.weekday()
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes)
    num_semanas = len(lunes_unicos)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    
    print("Construyendo modelo de prueba...")
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados=empleados,
        demanda_turnos=config_turnos,
        turnos_dict=turnos_dict,
        demanda_req=demanda_req,
        ajustes_demanda=ajustes_db,
        dias_del_bloque=dias_del_bloque,
        feriados=feriados_indices,
        offset_dia=offset_dia,
        num_semanas=num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False
    )
    
    # Buscar ABELENDA GRISELL
    emp_target = None
    for emp in empleados:
        if "ABELENDA" in emp.nombre.upper():
            emp_target = emp
            break
            
    if emp_target:
        print(f"\n--- Diagnóstico para {emp_target.nombre} ---")
        # Mostrar las claves en vars_turno_sem para este empleado
        print("Claves en ctx.vars_turno_sem para el empleado:")
        for k in ctx.vars_turno_sem.keys():
            if k[0] == emp_target.nombre:
                print(f"  {k}")
                
        # Mostrar el historial de la semana previa cargado
        hist_prev = historial_semana_previa.get(emp_target.nombre, [])
        print(f"\nHistorial semana previa de {emp_target.nombre}:")
        for h in hist_prev:
            print(f"  Fecha: {h['fecha']}, Turno: {h['turno']}, Horas: {h['horas']}")
            
        # Simular lo que hace la regla esquema_semanal_enfermeria
        from restricciones.hard._utils import get_semanas_calendario
        semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
        print("\nSemanas calendario detectadas:")
        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            v_dict = ctx.vars_turno_sem.get((emp_target.nombre, fecha_lunes))
            
            prev_sem = [h for h in hist_prev
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            prev_turnos_12h = sum(1 for h in prev_sem if h['turno'] in ['MT', 'TNN'])
            
            vars_turnos = [
                ctx.turnos[(emp_target.nombre, d, t)]
                for d, _ in days
                for t in ['MT', 'TNN']
                if (emp_target.nombre, d, t) in ctx.turnos
            ]
            
            print(f"Semana {iso_y}W{iso_w}: lunes={fecha_lunes}, v_dict_exists={v_dict is not None}, prev_12h={prev_turnos_12h}, vars_turnos_len={len(vars_turnos)}")
    else:
        print("No se encontró a ABELENDA GRISELL en los empleados.")

if __name__ == "__main__":
    debug()
