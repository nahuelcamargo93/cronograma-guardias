"""restricciones/hard/rotacion_mensual_dura.py — Obliga a usar al menos N familias de turno por mes."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    for emp in ctx.empleados:
        nombre = emp.nombre
        dias_bloq = emp.dias_licencia

        sem_vars = {'M': [], 'T': [], 'TN': [], 'N': []}
        for sem_key in dias_por_semana:
            v_dict = ctx.vars_turno_sem.get((nombre, sem_key))
            if v_dict:
                for k in sem_vars: sem_vars[k].append(v_dict[k])

        params = _re.resolver_parametros_regla(
            'PENALIZACION_TURNO_AUSENTE', nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params): continue

        has_family = {}
        for t_code, svars in sem_vars.items():
            if svars:
                hf = modelo.NewBoolVar(f'has_fam_hard_{t_code}_{nombre}')
                modelo.Add(sum(svars) >= 1).OnlyEnforceIf(hf)
                modelo.Add(sum(svars) == 0).OnlyEnforceIf(hf.Not())
                has_family[t_code] = hf

        semanas_disp = sum(
            1 for sem_key, dias_s in dias_por_semana.items()
            if len(dias_s) >= 4 and sum(1 for d in dias_s if d not in dias_bloq) >= 4
        )
        req = min(4, semanas_disp)
        if req > 0 and has_family:
            add_hard(modelo, ctx,
                     modelo.Add(sum(has_family.values()) >= req),
                     nombre)
