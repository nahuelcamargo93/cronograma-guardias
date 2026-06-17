"""
restricciones/hard/brecha_diaria_personal.py — DOUBLE (modo configurable HARD/SOFT)
Nivela al personal por puesto y franja horaria a lo largo de los días de la semana y fin de semana.
Regla: PESO_BRECHA_DIARIA_PERSONAL
"""
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
from datetime import date, timedelta
from utils import time_to_float
import rule_engine as _re


def apply(modelo, ctx) -> None:
    ref_fecha = ctx.fecha_inicio
    p_regla = _re.resolver_parametros_regla(
        'PESO_BRECHA_DIARIA_PERSONAL', 'GLOBAL', ref_fecha, ctx.reglas_servicio, {}, {}
    )
    if not _re.regla_existe(p_regla) or _re.regla_suspendida(p_regla):
        return

    modo = p_regla.get('modo', 'SOFT').upper() if isinstance(p_regla, dict) else 'SOFT'
    max_brecha = p_regla.get('max_brecha', 1) if isinstance(p_regla, dict) else 1
    peso_brecha = p_regla.get('peso_brecha', 100) if isinstance(p_regla, dict) else 100
    peso_cobertura = p_regla.get('peso_cobertura', 10) if isinstance(p_regla, dict) else 10

    # 1. Nivelación de brecha diaria por puesto/turno
    todos_turnos = list(ctx.turnos_dict.keys())
    for t_nombre in todos_turnos:
        for tipo_dia in ["Semana", "Finde_Feriado"]:
            # Obtener días del tipo correspondiente
            dias_tipo = [
                d for d in range(ctx.dias)
                if ("Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana") == tipo_dia
            ]
            if not dias_tipo:
                continue

            totales_dias_t = []
            for d in dias_tipo:
                vars_dia_t = [
                    ctx.turnos[(emp.nombre, d, t_nombre)]
                    for emp in ctx.empleados
                    if (emp.nombre, d, t_nombre) in ctx.turnos
                ]
                if vars_dia_t:
                    totales_dias_t.append(sum(vars_dia_t))

            # Solo definir brecha si hay al menos 2 días con variables
            if len(totales_dias_t) >= 2:
                max_dia_t = modelo.NewIntVar(0, len(ctx.empleados), f'max_dia_t_{t_nombre}_{tipo_dia}')
                min_dia_t = modelo.NewIntVar(0, len(ctx.empleados), f'min_dia_t_{t_nombre}_{tipo_dia}')

                modelo.AddMaxEquality(max_dia_t, totales_dias_t)
                modelo.AddMinEquality(min_dia_t, totales_dias_t)

                brecha_t = modelo.NewIntVar(0, len(ctx.empleados), f'brecha_diaria_t_{t_nombre}_{tipo_dia}')
                modelo.Add(brecha_t == max_dia_t - min_dia_t)

                if modo == 'HARD':
                    add_hard(modelo, ctx,
                             modelo.Add(brecha_t <= max_brecha),
                             f"{t_nombre}_{tipo_dia}")
                else:  # SOFT
                    ctx.penalizaciones_soft.append(brecha_t * peso_brecha)

    # 2. Minimizar déficit de cobertura (acercar cantidad a cantidad_max)
    if peso_cobertura > 0 and ctx.demanda_req:
        fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
        for d in range(ctx.dias):
            es_f = is_finde(d, ctx.offset_dia, ctx.feriados)
            tipo_dia = "Finde_Feriado" if es_f else "Semana"
            fecha_actual_iso = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            dia_semana_actual = (d + ctx.offset_dia) % 7

            demandas_por_ventana = {}
            for demanda in ctx.demanda_req.get(tipo_dia, []):
                key = (demanda["hora_inicio"], demanda["hora_fin"])
                demandas_por_ventana.setdefault(key, []).append(demanda)

            for (h_start, h_end), window_demands in demandas_por_ventana.items():
                d_h_start = time_to_float(h_start)
                d_h_end = time_to_float(h_end)
                d_abs_start = d * 24 + d_h_start
                if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                    d_abs_end = (d + 1) * 24 + d_h_end
                elif d_h_end == 0 and d_h_start > 0:
                    d_abs_end = (d + 1) * 24
                else:
                    d_abs_end = d * 24 + d_h_end

                for dem in window_demands:
                    c_max = dem.get("cantidad_max")
                    if c_max is None or c_max <= 0:
                        continue

                    # Buscar si hay ajuste de demanda
                    aj_o = None
                    if ctx.ajustes_demanda:
                        for (fi, ff), cambios in ctx.ajustes_demanda.items():
                            if fi <= fecha_actual_iso <= ff:
                                for adj in cambios:
                                    if adj["demanda_config_id"] == dem["id"]:
                                        aj_o = adj
                                        break
                    if aj_o:
                        if aj_o["dias_override"]:
                            dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                            if dia_semana_actual not in dias_validos and d not in ctx.feriados:
                                c_max = 0
                            else:
                                c_max = aj_o.get("cantidad_max")
                        else:
                            c_max = aj_o.get("cantidad_max")

                    if c_max is None or c_max <= 0:
                        continue

                    # Construir pool de variables normales que cubren esta ventana
                    pool_normales = []
                    for emp in ctx.empleados:
                        if d in emp.dias_licencia:
                            continue

                        # Cargar si es extra
                        fecha_bloque = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
                        params_extra = _re.resolver_parametros_regla(
                            'PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque,
                            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                        )
                        es_extra = False
                        if _re.regla_existe(params_extra) and isinstance(params_extra, dict):
                            nombres_extra_resueltos = params_extra.get('nombres', [])
                            if emp.nombre in nombres_extra_resueltos:
                                es_extra = True

                        if es_extra:
                            continue

                        for t_nombre, t_info in ctx.turnos_dict.items():
                            if t_info.puesto_nombre != dem["puesto"]:
                                continue
                            if (emp.nombre, d, t_nombre) in ctx.turnos:
                                ts_abs = d * 24 + time_to_float(t_info.hora_inicio)
                                te_abs = ts_abs + t_info.horas
                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                    pool_normales.append(ctx.turnos[(emp.nombre, d, t_nombre)])

                    if pool_normales:
                        deficit_var = modelo.NewIntVar(0, c_max, f'deficit_{dem["id"]}_d{d}')
                        modelo.Add(deficit_var >= c_max - sum(pool_normales))
                        ctx.penalizaciones_soft.append(deficit_var * peso_cobertura)
