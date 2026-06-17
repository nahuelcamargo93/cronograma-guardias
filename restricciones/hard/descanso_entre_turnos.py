"""
restricciones/hard/descanso_entre_turnos.py — DOUBLE (modo configurable HARD/SOFT)
Asegura que cada profesional tenga un descanso mínimo obligatorio entre turnos.
Regla: DESCANSO_ENTRE_TURNOS
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
from utils import time_to_float
import rule_engine as _re


def apply(modelo, ctx) -> None:
    if 'DESCANSO_ENTRE_TURNOS' not in ctx.reglas_servicio:
        return

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    for emp in ctx.empleados:
        for d1 in range(ctx.dias):
            fecha_d1 = (fecha_inicio_dt + timedelta(days=d1)).isoformat()
            params = _re.resolver_parametros_regla(
                'DESCANSO_ENTRE_TURNOS', emp.nombre, fecha_d1,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or _re.regla_suspendida(params):
                continue

            descansos_por_turno = {}
            horas_global = 12
            if isinstance(params, dict):
                descansos_por_turno = params.get('por_turno', {})
                horas_global = params.get('horas', 12)

            td1 = "Finde_Feriado" if is_finde(d1, ctx.offset_dia, ctx.feriados) else "Semana"
            for T1 in ctx.demanda_turnos.get(td1, {}).keys():
                if (emp.nombre, d1, T1) not in ctx.turnos:
                    continue

                R_T1 = descansos_por_turno.get(T1, horas_global)
                if R_T1 <= 0:
                    continue

                if T1 not in ctx.turnos_dict:
                    continue

                info_T1 = ctx.turnos_dict[T1]
                H_start_T1 = time_to_float(info_T1.hora_inicio)
                D_T1 = info_T1.horas
                H_fin_T1 = H_start_T1 + D_T1

                # Determinar rango de días futuros a inspeccionar
                max_dias_futuros = int((H_fin_T1 + R_T1) // 24) + 1

                for d2 in range(d1 + 1, min(ctx.dias, d1 + max_dias_futuros + 1)):
                    td2 = "Finde_Feriado" if is_finde(d2, ctx.offset_dia, ctx.feriados) else "Semana"
                    for T2 in ctx.demanda_turnos.get(td2, {}).keys():
                        if (emp.nombre, d2, T2) not in ctx.turnos:
                            continue

                        info_T2 = ctx.turnos_dict[T2]
                        H_start_T2 = time_to_float(info_T2.hora_inicio)

                        # Calcular descanso real transcurrido
                        descanso_real = (d2 - d1) * 24 + H_start_T2 - H_fin_T1

                        if descanso_real < R_T1:
                            etiqueta = f"{emp.nombre}_d{d1}{T1}_d{d2}{T2}".replace(" ", "_")
                            add_hard(modelo, ctx,
                                     modelo.Add(ctx.turnos[(emp.nombre, d1, T1)] + ctx.turnos[(emp.nombre, d2, T2)] <= 1),
                                     etiqueta)

        # Transición con el cronograma anterior (historial_semana_previa)
        if ctx.historial_semana_previa:
            hist_prev = ctx.historial_semana_previa.get(emp.nombre, [])
            for p in hist_prev:
                fecha_prev = date.fromisoformat(p['fecha'])
                T_prev = p['turno']

                params_prev = _re.resolver_parametros_regla(
                    'DESCANSO_ENTRE_TURNOS', emp.nombre, fecha_prev.isoformat(),
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )
                if not _re.regla_existe(params_prev) or _re.regla_suspendida(params_prev):
                    continue

                descansos_por_turno_prev = {}
                horas_global_prev = 12
                if isinstance(params_prev, dict):
                    descansos_por_turno_prev = params_prev.get('por_turno', {})
                    horas_global_prev = params_prev.get('horas', 12)

                R_prev = descansos_por_turno_prev.get(T_prev, horas_global_prev)
                if R_prev <= 0:
                    continue

                t_info_prev = ctx.turnos_dict.get(T_prev.replace(" ", "_"))
                if t_info_prev:
                    H_start_prev = time_to_float(t_info_prev.hora_inicio)
                else:
                    if "Noche" in T_prev: H_start_prev = 20.0
                    elif "Tarde" in T_prev: H_start_prev = 14.0
                    else: H_start_prev = 8.0

                D_prev = p.get('horas', 12)
                H_fin_prev = H_start_prev + D_prev

                # Analizar días iniciales del nuevo cronograma que entren en el rango de descanso
                max_d2_to_check = int((H_fin_prev + R_prev) // 24) + 1
                for d2 in range(min(ctx.dias, max_d2_to_check)):
                    fecha_d2 = fecha_inicio_dt + timedelta(days=d2)
                    d_diff = (fecha_d2 - fecha_prev).days
                    if d_diff < 0:
                        continue

                    td2 = "Finde_Feriado" if is_finde(d2, ctx.offset_dia, ctx.feriados) else "Semana"
                    for T2 in ctx.demanda_turnos.get(td2, {}).keys():
                        if (emp.nombre, d2, T2) not in ctx.turnos:
                            continue

                        info_T2 = ctx.turnos_dict[T2]
                        H_start_T2 = time_to_float(info_T2.hora_inicio)

                        descanso_real = d_diff * 24 + H_start_T2 - H_fin_prev
                        if descanso_real < R_prev:
                            etiqueta = f"{emp.nombre}_hist_{fecha_prev.isoformat()}_{T_prev}_to_d{d2}_{T2}".replace(" ", "_")
                            add_hard(modelo, ctx,
                                     modelo.Add(ctx.turnos[(emp.nombre, d2, T2)] == 0),
                                     etiqueta)

