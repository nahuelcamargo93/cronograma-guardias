"""restricciones/hard/cobertura_dinamica.py — Asegura la cobertura de demanda mínima y máxima por puesto y día."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from utils import time_to_float
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    historial = ctx.historial_semana_previa or {}

    for dia in range(ctx.dias):
        es_f = ((dia + ctx.offset_dia) % 7) >= 5 or dia in ctx.feriados
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_actual_iso = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
        dia_semana_actual = (dia + ctx.offset_dia) % 7

        # Agrupar demandas del día por puesto y ventana horaria (hora_inicio, hora_fin)
        candidates_by_window = {}
        for demanda in ctx.demanda_req.get(tipo_dia, []):
            dias_sem = demanda.get("dias_semana")
            applies = False
            if dias_sem:
                dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
                if dia_semana_actual in dias_validos:
                    applies = True
            else:
                if dia in ctx.feriados:
                    applies = True
                elif tipo_dia == "Semana" and dia_semana_actual in [0, 1, 2, 3, 4]:
                    applies = True
                elif tipo_dia == "Finde_Feriado" and dia_semana_actual in [5, 6]:
                    applies = True

            if applies:
                puesto_key = demanda.get("puesto_id")
                key = (puesto_key, demanda["hora_inicio"], demanda["hora_fin"])
                candidates_by_window.setdefault(key, []).append(demanda)

        # Para cada ventana de cada puesto, si hay específicas (con dias_semana), descartar las genéricas
        final_demandas = []
        for key, candidates in candidates_by_window.items():
            especificas = [c for c in candidates if c.get("dias_semana")]
            if especificas:
                final_demandas.extend(especificas)
            else:
                final_demandas.extend(candidates)

        # Agrupar demandas finales del día por ventana horaria (hora_inicio, hora_fin)
        demandas_por_ventana = {}
        for demanda in final_demandas:
            key = (demanda["hora_inicio"], demanda["hora_fin"])
            demandas_por_ventana.setdefault(key, []).append(demanda)

        for (h_start, h_end), window_demands in demandas_por_ventana.items():
            # Tiempos absolutos para esta ventana
            d_h_start = time_to_float(h_start)
            d_h_end = time_to_float(h_end)
            d_abs_start = dia * 24 + d_h_start
            if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                d_abs_end = (dia + 1) * 24 + d_h_end
            elif d_h_end == 0 and d_h_start > 0:
                d_abs_end = (dia + 1) * 24
            else:
                d_abs_end = dia * 24 + d_h_end

            # Identificar demandas específicas de esta ventana
            planta_dem = None
            residente_dem = None
            otras_dems = []

            for dem in window_demands:
                if dem["puesto"] == "Planta":
                    planta_dem = dem
                elif dem["puesto"] == "Residente":
                    residente_dem = dem
                else:
                    otras_dems.append(dem)

            # 1. Resolver y aplicar para Planta y Residente de forma combinada
            pool_planta_normales = []
            extra_planta_vars_in_window = []  # Colecciona variables de personal extra en esta ventana
            pool_residente_normales = []

            has_planta_block_vars = False
            has_residente_block_vars = False

            for emp in ctx.empleados:
                # Verificar regla de extra para este empleado hoy
                fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                params_extra = _re.resolver_parametros_regla(
                    'PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque,
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )

                is_special_extra = False
                if _re.regla_existe(params_extra) and isinstance(params_extra, dict):
                    nombres_extra_resueltos = params_extra.get('nombres', [])
                    if emp.nombre in nombres_extra_resueltos:
                        is_special_extra = True

                for d_off in [0, -1]:
                    dia_t = dia + d_off
                    if dia_t < 0:
                        if historial:
                            prev_guards = historial.get(emp.nombre, [])
                            fecha_ayer = (fecha_inicio_dt + timedelta(days=-1)).strftime("%Y-%m-%d")
                            for g in prev_guards:
                                if g['fecha'] == fecha_ayer:
                                    t_prev_nombre = g['turno']
                                    if t_prev_nombre in ctx.turnos_dict:
                                        t_info = ctx.turnos_dict[t_prev_nombre]
                                        ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
                                        te_abs = ts_abs + t_info.horas
                                        if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                            if t_info.puesto_nombre == "Planta":
                                                pool_planta_normales.append(1)
                                                if is_special_extra:
                                                    extra_planta_vars_in_window.append(1)
                                            elif t_info.puesto_nombre == "Residente":
                                                pool_residente_normales.append(1)
                        continue

                    if dia_t in emp.dias_licencia:
                        continue

                    for t_nombre, t_info in ctx.turnos_dict.items():
                        if (emp.nombre, dia_t, t_nombre) in ctx.turnos:
                            ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
                            te_abs = ts_abs + t_info.horas
                            if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                var = ctx.turnos[(emp.nombre, dia_t, t_nombre)]
                                if t_info.puesto_nombre == "Planta":
                                    pool_planta_normales.append(var)
                                    if dia_t >= 0:
                                        has_planta_block_vars = True
                                    if is_special_extra:
                                        extra_planta_vars_in_window.append(var)
                                elif t_info.puesto_nombre == "Residente":
                                    pool_residente_normales.append(var)
                                    if dia_t >= 0:
                                        has_residente_block_vars = True

            # Resolver límites para Planta
            if planta_dem:
                p_min = planta_dem.get("cantidad_min")
                p_max = planta_dem.get("cantidad_max")

                # Buscar ajustes de demanda Planta
                aj_p = None
                for (fi, ff), cambios in ctx.ajustes_demanda.items():
                    if fi <= fecha_actual_iso <= ff:
                        for adj in cambios:
                            if adj["demanda_config_id"] == planta_dem["id"]:
                                aj_p = adj
                                break
                if aj_p:
                    if aj_p["dias_override"]:
                        dias_validos = [int(x) for x in aj_p["dias_override"].split(",")]
                        if dia_semana_actual in dias_validos or dia in ctx.feriados:
                            p_min = aj_p.get("cantidad_min")
                            p_max = aj_p.get("cantidad_max")
                    else:
                        p_min = aj_p.get("cantidad_min")
                        p_max = aj_p.get("cantidad_max")

                # Aplicar restricciones Planta
                if p_min is not None and p_min > 0:
                    if d_abs_end <= 8 and not has_planta_block_vars:
                        pass
                    else:
                        add_hard(modelo, ctx,
                                 modelo.Add(sum(pool_planta_normales) >= p_min),
                                 f"min_planta_dia{dia}_h{h_start}")
                if p_max is not None:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(pool_planta_normales) <= p_max),
                             f"max_planta_dia{dia}_h{h_start}")

            # Resolver límites para Residente
            if residente_dem:
                r_min = residente_dem.get("cantidad_min")
                r_max = residente_dem.get("cantidad_max")

                # Buscar ajustes de demanda Residente
                aj_r = None
                for (fi, ff), cambios in ctx.ajustes_demanda.items():
                    if fi <= fecha_actual_iso <= ff:
                        for adj in cambios:
                            if adj["demanda_config_id"] == residente_dem["id"]:
                                aj_r = adj
                                break
                if aj_r:
                    if aj_r["dias_override"]:
                        dias_validos = [int(x) for x in aj_r["dias_override"].split(",")]
                        if dia_semana_actual in dias_validos or dia in ctx.feriados:
                            r_min = aj_r.get("cantidad_min")
                            r_max = aj_r.get("cantidad_max")
                    else:
                        r_min = aj_r.get("cantidad_min")
                        r_max = aj_r.get("cantidad_max")

                # Aplicar restricciones Residente con incremento dinámico por médicos de planta extra
                if r_min is not None and r_min > 0:
                    if d_abs_end <= 8 and not has_residente_block_vars:
                        pass
                    else:
                        if extra_planta_vars_in_window:
                            for var in extra_planta_vars_in_window:
                                add_hard(modelo, ctx,
                                         modelo.Add(sum(pool_residente_normales) >= r_min + var),
                                         f"min_residente_extra_dia{dia}_h{h_start}")
                        add_hard(modelo, ctx,
                                 modelo.Add(sum(pool_residente_normales) >= r_min),
                                 f"min_residente_dia{dia}_h{h_start}")
                if r_max is not None:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(pool_residente_normales) <= r_max),
                             f"max_residente_dia{dia}_h{h_start}")

            # 2. Manejar otras demandas normales (por compatibilidad si existen)
            for dem in otras_dems:
                c_min = dem.get("cantidad_min")
                c_max = dem.get("cantidad_max")

                aj_o = None
                for (fi, ff), cambios in ctx.ajustes_demanda.items():
                    if fi <= fecha_actual_iso <= ff:
                        for adj in cambios:
                            if adj["demanda_config_id"] == dem["id"]:
                                aj_o = adj
                                break
                if aj_o:
                    if aj_o["dias_override"]:
                        dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                        if dia_semana_actual in dias_validos or dia in ctx.feriados:
                            c_min = aj_o.get("cantidad_min")
                            c_max = aj_o.get("cantidad_max")
                    else:
                        c_min = aj_o.get("cantidad_min")
                        c_max = aj_o.get("cantidad_max")

                if c_min is None and c_max is None:
                    continue

                pool_normales = []
                pool_extras = []
                has_block_vars = False

                for emp in ctx.empleados:
                    fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                    params_extra = _re.resolver_parametros_regla(
                        'PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque,
                        ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                    )
                    es_extra = False
                    if _re.regla_existe(params_extra) and isinstance(params_extra, dict):
                        nombres_extra_resueltos = params_extra.get('nombres', [])
                        if emp.nombre in nombres_extra_resueltos:
                            es_extra = True

                    for d_off in [0, -1]:
                        dia_t = dia + d_off
                        if dia_t < 0:
                            if historial:
                                prev_guards = historial.get(emp.nombre, [])
                                fecha_ayer = (fecha_inicio_dt + timedelta(days=-1)).strftime("%Y-%m-%d")
                                for g in prev_guards:
                                    if g['fecha'] == fecha_ayer:
                                        t_prev_nombre = g['turno']
                                        if t_prev_nombre in ctx.turnos_dict:
                                            t_info = ctx.turnos_dict[t_prev_nombre]
                                            ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
                                            te_abs = ts_abs + t_info.horas
                                            if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                                if es_extra:
                                                    pool_extras.append(1)
                                                else:
                                                    pool_normales.append(1)
                            continue

                        if dia_t in emp.dias_licencia:
                            continue

                        for t_nombre, t_info in ctx.turnos_dict.items():
                            if t_info.puesto_nombre != dem["puesto"]:
                                continue
                            if (emp.nombre, dia_t, t_nombre) in ctx.turnos:
                                ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
                                te_abs = ts_abs + t_info.horas
                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                    if es_extra:
                                        pool_extras.append(ctx.turnos[(emp.nombre, dia_t, t_nombre)])
                                    else:
                                        pool_normales.append(ctx.turnos[(emp.nombre, dia_t, t_nombre)])
                                        if dia_t >= 0:
                                            has_block_vars = True

                if c_min is not None and c_min > 0:
                    if d_abs_end <= 8 and not has_block_vars:
                        pass
                    else:
                        add_hard(modelo, ctx,
                                 modelo.Add(sum(pool_normales) >= c_min),
                                 f"min_{dem['puesto']}_dia{dia}_h{h_start}")
                if c_max is not None:
                    add_hard(modelo, ctx,
                             modelo.Add(sum(pool_normales) + sum(pool_extras) <= c_max),
                             f"max_{dem['puesto']}_dia{dia}_h{h_start}")
