"""restricciones/hard/max_francos_semana.py — Límite máximo de francos por semana calendario."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import rule_engine as _re

def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'MAX_FRANCOS_SEMANA', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        limite = params.get('limite', 3) if isinstance(params, dict) else 3
        modo = params.get('modo', 'HARD').upper() if isinstance(params, dict) else 'HARD'
        peso_soft = params.get('peso_soft', 10000) if isinstance(params, dict) else 10000

        for (iso_y, iso_w), days in semanas.items():
            # 3. Ignorar semanas incompletas (limítrofes del mes) para evitar problemas de bordes
            if len(days) < 7:
                continue

            francos_present = []
            all_work_vars = []

            for d_idx, _ in days:
                if d_idx in emp.dias_licencia:
                    continue

                td = "Finde_Feriado" if is_finde(d_idx, ctx.offset_dia, ctx.feriados) else "Semana"
                turnos_dia = [ctx.turnos[(emp.nombre, d_idx, t)]
                              for t in ctx.demanda_turnos.get(td, {}).keys()
                              if (emp.nombre, d_idx, t) in ctx.turnos]
                
                if turnos_dia:
                    is_work = sum(turnos_dia)
                    all_work_vars.append(is_work)
                    
                    is_franco = modelo.NewBoolVar(f"franco_{emp.nombre}_d{d_idx}")
                    modelo.Add(is_franco == 1 - is_work)
                    francos_present.append(is_franco)

            if francos_present:
                # 4. La semana está activa si el empleado trabaja al menos 1 día.
                # Nota: v_dict (vars_turno_sem) NO es confiable para esto porque
                # las variables is_M/T/N son implicaciones unidireccionales y
                # siempre existe el dict aunque la semana esté vacía.
                semana_activa = modelo.NewBoolVar(f"sem_act_{emp.nombre}_{iso_y}w{iso_w}")
                total_work_in_week = sum(all_work_vars)
                modelo.Add(total_work_in_week >= 1).OnlyEnforceIf(semana_activa)
                modelo.Add(total_work_in_week == 0).OnlyEnforceIf(semana_activa.Not())

                # Buscar variables de FLR que se superponen con esta semana para ajustar el límite
                semana_days = [d for d, _ in days]
                semana_set = set(semana_days)
                min_d = min(semana_days)
                max_d = max(semana_days)
                ajuste_terms = []

                if ctx.flr_tracker:
                    for d_start in range(min_d - 3, max_d + 1):
                        if (emp.nombre, d_start) in ctx.flr_tracker:
                            var_flr = ctx.flr_tracker[(emp.nombre, d_start)]
                            flr_dias = {d_start, d_start + 1, d_start + 2, d_start + 3}
                            k = len(flr_dias.intersection(semana_set))
                            coef = max(0, k - limite)
                            if coef > 0:
                                ajuste_terms.append(var_flr * coef)

                # Contar días de franco forzado manual en esta semana
                cant_francos_forzados = 0
                for d_idx, fecha_d in days:
                    fecha_d_str = fecha_d.isoformat()
                    p_ff = _re.resolver_parametros_regla(
                        'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                        ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                    )
                    if _re.regla_existe(p_ff) and not _re.regla_suspendida(p_ff):
                        cant_francos_forzados += 1

                ajuste_ff = max(0, cant_francos_forzados - limite)

                limite_final = limite + ajuste_ff
                if modo == "HARD":
                    if ajuste_terms:
                        ct = modelo.Add(sum(francos_present) <= limite_final + sum(ajuste_terms))
                    else:
                        ct = modelo.Add(sum(francos_present) <= limite_final)
                    ct.OnlyEnforceIf(semana_activa)
                    add_hard(modelo, ctx, ct, f"{emp.nombre}_{iso_y}w{iso_w}")
                else:  # SOFT
                    v_viol = modelo.NewIntVar(0, 7, f"viol_max_fr_{emp.nombre}_{iso_y}w{iso_w}")
                    if ajuste_terms:
                        modelo.Add(sum(francos_present) <= limite_final + sum(ajuste_terms) + v_viol).OnlyEnforceIf(semana_activa)
                    else:
                        modelo.Add(sum(francos_present) <= limite_final + v_viol).OnlyEnforceIf(semana_activa)
                    
                    modelo.Add(v_viol == 0).OnlyEnforceIf(semana_activa.Not())
                    ctx.penalizaciones_soft.append(v_viol * peso_soft)
