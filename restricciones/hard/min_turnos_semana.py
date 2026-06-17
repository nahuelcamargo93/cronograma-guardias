"""restricciones/hard/min_turnos_semana.py — Piso mínimo de turnos trabajados por semana calendario.

Esta regla asegura que el profesional trabaje al menos una cantidad mínima de turnos en cada semana
calendario. Permite configurar modo HARD o SOFT y contempla las licencias del profesional como días
trabajados en dicha semana (reduciendo correspondientemente el requerimiento).
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import database.queries as q
import rule_engine as _re

def es_fecha_licencia(nombre: str, fecha_dt: date) -> bool:
    for licencias in (q.LAR, q.LPP, q.LM, q.CM):
        for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
            if date.fromisoformat(lic_ini_str) <= fecha_dt <= date.fromisoformat(lic_fin_str):
                return True
    return False

def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
    historial = ctx.historial_semana_previa or {}

    for emp in ctx.empleados:
        hist_emp = historial.get(emp.nombre, [])
        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            
            # Obtener parámetros para el empleado y la semana correspondiente
            params = _re.resolver_parametros_regla(
                'MIN_TURNOS_SEMANA', emp.nombre, fecha_lunes,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            if not _re.regla_existe(params) or _re.regla_suspendida(params):
                continue
                
            min_turnos = params.get('min_turnos', 4) if isinstance(params, dict) else 4
            modo = params.get('modo', 'HARD').upper() if isinstance(params, dict) else 'HARD'
            peso_soft = params.get('peso_soft', 100_000) if isinstance(params, dict) else 100_000

            # 1. Contar turnos trabajados en el historial que pertenecen a esta semana
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            turnos_prev = len(prev_sem)

            # 2. Contar licencias en el historial que corresponden a esta semana
            # Las licencias en el historial (días antes de fecha_inicio_dt) cuentan como días trabajados
            licencias_prev = 0
            dias_prev = 0
            lunes_dt = fl - timedelta(days=fl.isocalendar()[2] - 1)
            for offset in range(7):
                dia_semana_dt = lunes_dt + timedelta(days=offset)
                if dia_semana_dt < fecha_inicio_dt:
                    dias_prev += 1
                    if es_fecha_licencia(emp.nombre, dia_semana_dt):
                        licencias_prev += 1

            # Escalar el requerimiento si la semana calendario está incompleta (bordes del mes)
            dias_conocidos = len(days) + dias_prev
            if dias_conocidos < 7:
                min_turnos_req = round(min_turnos * dias_conocidos / 7)
            else:
                min_turnos_req = min_turnos

            # Capar dinámicamente según horas mensuales reglamentarias y duración de turnos, o borrador del mes actual, o historial
            turnos_esperados_mes = None
            if emp.horas_mensuales_reglamentarias and emp.horas_mensuales_reglamentarias > 0:
                horas_habilitadas = []
                for d, _ in days:
                    td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                    for t in ctx.demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in ctx.turnos:
                            if t in ctx.turnos_dict:
                                horas_habilitadas.append(ctx.turnos_dict[t].horas)
                if horas_habilitadas:
                    duracion_turno = max(horas_habilitadas)
                    turnos_esperados_mes = emp.horas_mensuales_reglamentarias / duracion_turno

            # Si no hay horas reglamentarias, buscar si hay guardias precargadas en borrador para el mes actual
            if turnos_esperados_mes is None:
                try:
                    with q.get_connection() as conn:
                        row = conn.execute("""
                            SELECT COUNT(*) FROM guardias 
                            WHERE nombre = ? AND fecha BETWEEN ? AND ?
                        """, (emp.nombre, ctx.fecha_inicio, ctx.fecha_fin)).fetchone()
                        turnos_mes_actual = row[0] if row else 0
                    if turnos_mes_actual > 0:
                        turnos_esperados_mes = turnos_mes_actual
                except Exception:
                    pass

            # Fallback al historial de guardias del mes anterior si no hay guardias en el mes actual
            if turnos_esperados_mes is None:
                if hist_emp:
                    turnos_esperados_mes = len(hist_emp)
                else:
                    turnos_esperados_mes = 0  # Evitar forzar mínimos en personal inactivo/sin historial

            if turnos_esperados_mes is not None:
                semanas_mes = ctx.dias / 7.0
                max_turnos_prom_sem = turnos_esperados_mes / semanas_mes
                min_turnos_req = min(min_turnos_req, max(0, int(max_turnos_prom_sem)))

            if min_turnos_req <= 0:
                continue

            # 3. Variables de decisión de turnos asignados en la planificación actual para esta semana
            # Y licencias de la planificación actual
            turnos_sem = []
            licencias_plan = 0
            
            for d, _ in days:
                if d in emp.dias_licencia:
                    licencias_plan += 1
                    continue  # Es licencia, no se le asigna turno
                
                # Sumamos la asignación de cualquier turno en el día (a lo sumo 1 por la regla universal)
                turnos_dia = []
                for td in ["Semana", "Finde_Feriado"]:
                    for t in ctx.demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in ctx.turnos:
                            turnos_dia.append(ctx.turnos[(emp.nombre, d, t)])
                if turnos_dia:
                    turnos_sem.append(sum(turnos_dia))

            # Para evitar inviabilidad si no es físicamente posible cumplir el mínimo,
            # calculamos el límite superior teórico de turnos que podría trabajar en los días activos:
            t_max_plan = 0
            for d, _ in days:
                if d in emp.dias_licencia:
                    continue  # El profesional no trabaja en días de licencia
                
                td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                turnos_habilitados = [
                    t for t in ctx.demanda_turnos.get(td, {}).keys()
                    if (emp.nombre, d, t) in ctx.turnos
                ]
                if turnos_habilitados:
                    t_max_plan += 1

            limite_teorico = turnos_prev + licencias_prev + licencias_plan + t_max_plan
            piso = min(min_turnos_req, limite_teorico)

            total_turnos_lic_actual = sum(turnos_sem) + licencias_plan
            total_total = total_turnos_lic_actual + turnos_prev + licencias_prev

            # Si no hay turnos planificados posibles, ni historial, ni licencias, no tiene sentido restringir
            if not turnos_sem and turnos_prev == 0 and licencias_prev == 0 and licencias_plan == 0:
                continue

            if modo == "SOFT":
                nombre_limpio = emp.nombre.replace(" ", "_").replace(",", "")
                deficit = modelo.NewIntVar(0, piso, f"deficit_min_t_sem_{nombre_limpio}_{iso_y}w{iso_w}")
                modelo.Add(deficit >= piso - total_total)
                ctx.penalizaciones_soft.append(deficit * peso_soft)
            else:
                add_hard(modelo, ctx,
                         modelo.Add(total_total >= piso),
                         f"{emp.nombre}_{iso_y}w{iso_w}")
