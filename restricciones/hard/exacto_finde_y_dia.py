"""restricciones/hard/exacto_finde_y_dia.py — Regla unificada de fines de semana + día específico."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re

_MAPA = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
         "viernes": 4, "sabado": 5, "domingo": 6}
_NORM = str.maketrans("éáíóúÉÁÍÓÚ", "eaiouEAIOU")


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'EXACTO_FINDE_Y_DIA', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params): continue

        modo = params.get('modo', 'HARD').upper()
        peso_soft = params.get('peso_soft', 100000)

        dia_conf = params.get('dia_semana', 4)
        dia_str = str(dia_conf).lower().translate(_NORM)
        dia_target = _MAPA.get(dia_str, int(dia_conf) if str(dia_conf).isdigit() else 4)

        # Calcular disponibilidad fines de semana
        findes = {}
        for d in range(ctx.dias):
            if is_finde(d, ctx.offset_dia, ctx.feriados):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=fd.weekday())).isoformat()
                findes.setdefault(lunes, []).append(d)
        k = sum(1 for _, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))

        # Calcular disponibilidad día específico
        k_dia = 0
        for d in range(ctx.dias):
            if (fecha_inicio_dt + timedelta(days=d)).weekday() != dia_target: continue
            if d in emp.dias_licencia: continue
            k_dia += 1

        # Targets
        mf = params.get('findes_por_disponibilidad')
        target_f = (mf.get(str(k), mf.get(k, 0)) if isinstance(mf, dict) else
                    (2 if k >= 3 else (1 if k >= 1 else 0)))
        md = params.get('dias_por_disponibilidad')
        target_d = (md.get(str(k_dia), md.get(k_dia, 0)) if isinstance(md, dict) else
                    (2 if k_dia == 5 else (1 if k_dia in (4, 2) else 0)))

        # Aplicar fines de semana
        vars_f = []
        for lunes, dias in findes.items():
            dias_hab = [d for d in dias if d not in emp.dias_licencia and not (
                _re.regla_existe(p := _re.resolver_parametros_regla(
                    'FRANCO_FORZADO', emp.nombre,
                    (fecha_inicio_dt + timedelta(days=d)).isoformat(),
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )) and not _re.regla_suspendida(p)
            )]
            if not dias_hab: continue
            v_f = modelo.NewBoolVar(f'traba_fyd_{emp.nombre}_{lunes}')
            pool = [ctx.turnos[(emp.nombre, d, t)]
                    for d in dias_hab
                    for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                    if (emp.nombre, d, t) in ctx.turnos]
            if pool:
                modelo.AddMaxEquality(v_f, pool)
                vars_f.append(v_f)

        target_f_real = min(target_f, len(vars_f)) if vars_f else 0

        if vars_f:
            if modo == "HARD":
                add_hard(modelo, ctx,
                         modelo.Add(sum(vars_f) == target_f_real),
                         f"{emp.nombre}_finde")
            else: # SOFT
                violation_under = modelo.NewIntVar(0, target_f_real, f'viol_under_findes_combo_{emp.nombre}')
                violation_over = modelo.NewIntVar(0, len(vars_f), f'viol_over_findes_combo_{emp.nombre}')
                modelo.Add(sum(vars_f) + violation_under - violation_over == target_f_real)
                
                violation = modelo.NewIntVar(0, len(vars_f) + target_f_real, f'viol_findes_combo_{emp.nombre}')
                modelo.Add(violation == violation_under + violation_over)
                ctx.penalizaciones_soft.append(violation * peso_soft)

        # Contar asignaciones fijas en el día específico
        cant_asig_fijas = sum(
            1 for d in range(ctx.dias)
            if (fecha_inicio_dt + timedelta(days=d)).weekday() == dia_target
            and d not in emp.dias_licencia
            and _re.regla_existe(_re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre,
                (fecha_inicio_dt + timedelta(days=d)).isoformat(),
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            ))
        )

        vars_dia = []
        for d in range(ctx.dias):
            if (fecha_inicio_dt + timedelta(days=d)).weekday() != dia_target: continue
            if d in emp.dias_licencia: continue
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p_franco = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco): continue
            v = modelo.NewBoolVar(f'traba_dia_fyd_{emp.nombre}_{dia_target}_{d}')
            pool = [ctx.turnos[(emp.nombre, d, t)]
                    for t in ctx.turnos_dict.keys()
                    if (emp.nombre, d, t) in ctx.turnos]
            if pool:
                modelo.AddMaxEquality(v, pool)
                vars_dia.append(v)

        target_d_real = min(target_d, len(vars_dia)) if vars_dia else 0
        if cant_asig_fijas > 0:
            target_d_real = max(target_d_real, cant_asig_fijas)

        if vars_dia:
            if modo == "HARD":
                add_hard(modelo, ctx,
                         modelo.Add(sum(vars_dia) == target_d_real),
                         f"{emp.nombre}_dia{dia_target}")
            else: # SOFT
                violation_under = modelo.NewIntVar(0, target_d_real, f'viol_under_dia_combo_{emp.nombre}_{dia_target}')
                violation_over = modelo.NewIntVar(0, len(vars_dia), f'viol_over_dia_combo_{emp.nombre}_{dia_target}')
                modelo.Add(sum(vars_dia) + violation_under - violation_over == target_d_real)
                
                violation = modelo.NewIntVar(0, len(vars_dia) + target_d_real, f'viol_dia_combo_{emp.nombre}_{dia_target}')
                modelo.Add(violation == violation_under + violation_over)
                ctx.penalizaciones_soft.append(violation * peso_soft)
