"""restricciones/hard/exacto_dia_especifico_mes.py — Regla para días específicos de la semana por mes (HARD y SOFT)."""
from datetime import date, timedelta
from collections import defaultdict
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re

_MAPA = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
         "viernes": 4, "sabado": 5, "domingo": 6}
_NORM = str.maketrans("éáíóúÉÁÍÓÚ", "eaiouEAIOU")


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    # 1. Agrupar findes por semana
    finde_por_semana = defaultdict(list)
    for d_f in range(ctx.dias):
        if is_finde(d_f, ctx.offset_dia, ctx.feriados):
            fecha_df = fecha_inicio_dt + timedelta(days=d_f)
            lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
            finde_por_semana[lunes_f].append(d_f)

    for emp in ctx.empleados:
        # --- CASO A: EXACTO_DIA_ESPECIFICO_MES_HARD (DURA) ---
        params_hard = _re.resolver_parametros_regla(
            'EXACTO_DIA_ESPECIFICO_MES_HARD', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        has_hard = _re.regla_existe(params_hard) and not _re.regla_suspendida(params_hard)

        # --- CASO B: EXACTO_DIA_ESPECIFICO_MES & MIN_DIA_ESPECIFICO_MES (SOFT) ---
        params_min = _re.resolver_parametros_regla(
            'MIN_DIA_ESPECIFICO_MES', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        params_exacto = _re.resolver_parametros_regla(
            'EXACTO_DIA_ESPECIFICO_MES', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        
        has_min = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
        has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
        
        if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
            has_exacto = False

        # --- RESOLVER CUÁL REGLA APLICAR ---
        if has_hard:
            # Si hay regla hard, la aplicamos de forma estricta
            _aplicar_regla_dia(modelo, ctx, emp, params_hard, is_hard=True, is_exact=True, finde_por_semana=finde_por_semana, fecha_inicio_dt=fecha_inicio_dt)
        else:
            # Si no hay hard, aplicamos la soft correspondientes
            if has_exacto or has_min:
                is_exact = has_exacto
                params_soft = params_exacto if has_exacto else params_min
                _aplicar_regla_dia(modelo, ctx, emp, params_soft, is_hard=False, is_exact=is_exact, finde_por_semana=finde_por_semana, fecha_inicio_dt=fecha_inicio_dt)


def _aplicar_regla_dia(modelo, ctx, emp, params, is_hard: bool, is_exact: bool, finde_por_semana, fecha_inicio_dt) -> None:
    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().translate(_NORM)
        dia_semana_target = _MAPA.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)

    # Contar asignaciones fijas en el día específico
    cant_asig_fijas = 0
    for d in range(ctx.dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() != dia_semana_target:
            continue
        if d in emp.dias_licencia:
            continue

        fecha_d_str = fecha_d.isoformat()
        params_fija = _re.resolver_parametros_regla(
            'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_existe(params_fija) and isinstance(params_fija, list):
            params_franco = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = _re.regla_existe(params_franco) and not _re.regla_suspendida(params_franco)

            for asig in params_fija:
                fecha_asig = asig.get('Fecha')
                dia_asig   = asig.get('Dia')
                
                es_por_fecha = bool(fecha_asig and fecha_asig == fecha_d_str)
                es_por_dia = bool(dia_asig and _MAPA.get(dia_asig.lower().translate(_NORM)) == dia_semana_target and d not in ctx.feriados)
                
                match = False
                if es_por_fecha:
                    match = True
                elif es_por_dia:
                    if not tiene_franco:
                        match = True

                if match:
                    cant_asig_fijas += 1
                    break

    exacto_dias = params.get('exacto_dias', params.get('min_dias', 1))
    
    # Calcular semanas disponibles (k)
    k = sum(1 for lunes_f, dias_f in finde_por_semana.items() if any(d_f not in emp.dias_licencia for d_f in dias_f))

    if params.get('dinamico_licencias', False):
        if dia_semana_target == 4: # Viernes
            if k == 5:
                target_dias = 2
            elif k in (4, 2):
                target_dias = 1
            else:
                target_dias = 0
        else:
            target_dias = exacto_dias
    else:
        target_dias = exacto_dias

    if target_dias == 0 and not is_exact:
        return

    vars_dia = []
    for d in range(ctx.dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() != dia_semana_target: continue
        if d in emp.dias_licencia: continue
        fecha_d_str = fecha_d.isoformat()
        p_franco = _re.resolver_parametros_regla(
            'FRANCO_FORZADO', emp.nombre, fecha_d_str,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        tiene_franco = _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco)

        tiene_fija_fecha = False
        params_fija = _re.resolver_parametros_regla(
            'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_existe(params_fija) and isinstance(params_fija, list):
            for asig in params_fija:
                if asig.get('Fecha') == fecha_d_str:
                    tiene_fija_fecha = True
                    break

        if tiene_franco and not tiene_fija_fecha:
            continue

        # Identificador único de variable
        prefix = "traba_dia_esp_hard" if is_hard else "traba_dia_esp_soft"
        v = modelo.NewBoolVar(f'{prefix}_{emp.nombre}_{dia_semana_target}_{d}')
        pool = [ctx.turnos[(emp.nombre, d, t)]
                for t in ctx.turnos_dict.keys()
                if (emp.nombre, d, t) in ctx.turnos]
        if pool:
            modelo.AddMaxEquality(v, pool)
            vars_dia.append(v)

    if vars_dia:
        target_real = min(target_dias, len(vars_dia))
        if cant_asig_fijas > 0:
            target_real = max(target_real, cant_asig_fijas)
        if is_hard:
            add_hard(modelo, ctx, modelo.Add(sum(vars_dia) == target_real), emp.nombre)
        else:
            # MODO SOFT
            if is_exact:
                violation_under = modelo.NewIntVar(0, target_real, f'viol_under_dia_esp_{emp.nombre}_{dia_semana_target}')
                violation_over = modelo.NewIntVar(0, len(vars_dia), f'viol_over_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(sum(vars_dia) + violation_under - violation_over == target_real)
                
                violation = modelo.NewIntVar(0, len(vars_dia) + target_real, f'viol_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(violation == violation_under + violation_over)
                ctx.penalizaciones_soft.append(violation * 100000)
            else:
                violation = modelo.NewIntVar(0, target_real, f'viol_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(violation >= target_real - sum(vars_dia))
                ctx.penalizaciones_soft.append(violation * 100000)
