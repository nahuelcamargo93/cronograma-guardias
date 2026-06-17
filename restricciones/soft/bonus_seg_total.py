"""
restricciones/soft/bonus_seg_total.py — SOFT
Bonifica semanas de seguimiento completas (>= 4 turnos del mismo tipo en L-V)
y suma puntos individuales por día de seguimiento.
Reglas: BONUS_SEG_TOTAL, BONUS_SEG_PUNTOS, PESO_INCONSISTENCIA
"""
from datetime import date, timedelta
import rule_engine as _re

_TURNOS_SEG_DEFECTO = ('Mañana_UTI', 'Mañana_UCO', 'Tarde_UTI', 'Tarde_UCO')


def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        lunes = (fecha_inicio_dt + timedelta(days=d))
        lunes = lunes - timedelta(days=lunes.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    puntos_seg = []
    semanas_seg_totales = []
    puntos_inconsistencia = []

    if not hasattr(ctx, 'vars_seg_emp'):
        ctx.vars_seg_emp = {}

    for emp in ctx.empleados:
        params_seg = _re.resolver_parametros_regla(
            'BONUS_SEG_TOTAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )

        for sem_key, dias_sem in dias_por_semana.items():
            sem_id = sem_key.replace('-', '_')
            lv = [d for d in dias_sem if (d + ctx.offset_dia) % 7 < 5]
            lv_disp = [d for d in lv if d not in emp.dias_licencia]

            # Puntos de seguimiento individuales por día
            params_puntos = _re.resolver_parametros_regla(
                'BONUS_SEG_PUNTOS', emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params_puntos) and not _re.regla_suspendida(params_puntos):
                for t in _TURNOS_SEG_DEFECTO:
                    for d in lv:
                        if (emp.nombre, d, t) in ctx.turnos:
                            puntos_seg.append(ctx.turnos[(emp.nombre, d, t)])


            # Semanas completas de seguimiento
            if not _re.regla_suspendida(params_seg):
                cumple_t_list = []
                turnos_semanales = list(ctx.demanda_turnos.get('Semana', {}).keys())
                for t in turnos_semanales:
                    # Si el turno empieza con Dia_, no evaluamos seguimiento individual para él,
                    # ya que se desdobla en Mañana_ y Tarde_ correspondientes.
                    if t.startswith('Dia_'):
                        continue

                    # Determinar si hay un turno de Día correspondiente que deba sumarse
                    t_dia = None
                    if t.startswith('Mañana_'):
                        suffix = t.replace('Mañana_', '')
                        t_dia = f"Dia_{suffix}"
                    elif t.startswith('Mañana'):
                        suffix = t.replace('Mañana', '')
                        t_dia = f"Dia_{suffix}"
                    elif t.startswith('Tarde_'):
                        suffix = t.replace('Tarde_', '')
                        t_dia = f"Dia_{suffix}"
                    elif t.startswith('Tarde'):
                        suffix = t.replace('Tarde', '')
                        t_dia = f"Dia_{suffix}"

                    t_vars = []
                    for d in lv_disp:
                        if (emp.nombre, d, t) in ctx.turnos:
                            t_vars.append(ctx.turnos[(emp.nombre, d, t)])
                        if t_dia and (emp.nombre, d, t_dia) in ctx.turnos:
                            t_vars.append(ctx.turnos[(emp.nombre, d, t_dia)])

                    if len(t_vars) >= 4:
                        cumple_t = modelo.NewBoolVar(f'cumple_seg_{t}_{emp.nombre}_{sem_id}')
                        modelo.Add(sum(t_vars) >= 4).OnlyEnforceIf(cumple_t)
                        modelo.Add(sum(t_vars) < 4).OnlyEnforceIf(cumple_t.Not())
                        cumple_t_list.append(cumple_t)
                
                if cumple_t_list:
                    cumple_ind = modelo.NewBoolVar(f'premio_seg_ind_{emp.nombre}_{sem_id}')
                    modelo.Add(cumple_ind == sum(cumple_t_list))
                    semanas_seg_totales.append(cumple_ind)
                    ctx.vars_seg_emp.setdefault(emp.nombre, []).append(cumple_ind)

            # Inconsistencia de mezcla de turnos en semana
            params_inc = _re.resolver_parametros_regla(
                'PESO_INCONSISTENCIA', emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_suspendida(params_inc):
                all_lv = [ctx.turnos[(emp.nombre, d, t)] for d in lv
                          for t in ctx.demanda_turnos.get('Semana', {}).keys()
                          if (emp.nombre, d, t) in ctx.turnos]
                if all_lv:
                    total_lv = modelo.NewIntVar(0, 5, f'total_lv_{emp.nombre}_{sem_id}')
                    modelo.Add(total_lv == sum(all_lv))
                    diffs = []
                    for t_tipo in _TURNOS_SEG_DEFECTO:
                        vt = [ctx.turnos[(emp.nombre, d, t_tipo)] for d in lv
                              if (emp.nombre, d, t_tipo) in ctx.turnos]
                        if vt:
                            diff = modelo.NewIntVar(0, 5, f'diff_{t_tipo}_{emp.nombre}_{sem_id}')
                            modelo.Add(diff == total_lv - sum(vt))
                            diffs.append(diff)
                    if diffs:
                        inc = modelo.NewIntVar(0, 5, f'inc_{emp.nombre}_{sem_id}')
                        modelo.AddMinEquality(inc, diffs)
                        puntos_inconsistencia.append(inc)

    # Construir penalizaciones y bonuses agregados
    peso_seg_totales = ctx.reglas_servicio.get('BONUS_SEG_TOTAL', {}).get('peso', 150)
    peso_puntos_seg = ctx.reglas_servicio.get('BONUS_SEG_PUNTOS', {}).get('peso', 5)
    peso_inconsistencia = ctx.reglas_servicio.get('PESO_INCONSISTENCIA', {}).get('peso', 100)

    if semanas_seg_totales:
        ctx.bonuses_soft.extend(
            [v * peso_seg_totales for v in semanas_seg_totales]
        )
    if puntos_seg:
        ctx.bonuses_soft.extend([v * peso_puntos_seg for v in puntos_seg])
    if puntos_inconsistencia:
        ctx.penalizaciones_soft.extend(
            [v * peso_inconsistencia for v in puntos_inconsistencia]
        )
