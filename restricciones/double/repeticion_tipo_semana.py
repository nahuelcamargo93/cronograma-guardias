"""restricciones/double/repeticion_tipo_semana.py — REGLA_REPETICION_TIPO_SEMANA

Solo puede repetirse en el mes el tipo de turno semanal (familia M/T/TN/N) con que
el empleado comienza (primera semana activa del mes). Los demás tipos deben aparecer
a lo sumo UNA vez en todo el mes.

Si el empleado tiene menos de 4 semanas activas (por licencias), no puede repetir
ningún tipo: todos deben ser distintos (máximo 1 aparición de cada familia).

La condición del tipo_inicio se resuelve matemáticamente usando las vars_turno_sem de
la primera semana activa como selector booleano, sin necesitar leer el historial.

Configuración en BD (servicios_reglas):
    {
        "modo": "SOFT",        # "HARD" o "SOFT"
        "peso_soft": 8000
    }
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard


def apply(modelo, ctx) -> None:
    params = ctx.reglas_servicio.get('REGLA_REPETICION_TIPO_SEMANA')
    if not params:
        return

    modo = params.get('modo', 'SOFT').upper()
    peso_soft = params.get('peso_soft', 8000)

    familias = ['M', 'T', 'TN', 'N']

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    # Construir mapa semana → lista de días (índices)
    dias_por_semana: dict[str, list[int]] = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    semanas_keys = sorted(dias_por_semana.keys())
    if not semanas_keys:
        return

    for emp in ctx.empleados:
        # ── 1. Determinar semanas con al menos 1 día activo (no licencia) ──────
        semanas_activas: list[str] = []
        for sem_key in semanas_keys:
            dias_sem = dias_por_semana[sem_key]
            hay_activo = any(d not in emp.dias_licencia for d in dias_sem)
            if hay_activo:
                semanas_activas.append(sem_key)

        if len(semanas_activas) < 2:
            continue  # Nada que restringir con tan pocas semanas

        n_activas = len(semanas_activas)

        # Recopilar vars_turno_sem solo para semanas activas
        vars_por_semana: dict[str, dict] = {}
        for sem_key in semanas_activas:
            v_dict = ctx.vars_turno_sem.get((emp.nombre, sem_key))
            if v_dict:
                vars_por_semana[sem_key] = v_dict

        if len(vars_por_semana) < 2:
            continue

        nombre_safe = emp.nombre.replace(' ', '_').replace(',', '').replace('-', '_')

        # ── 2. CASO A: < 4 semanas activas → no puede repetir ningún tipo ─────
        if n_activas < 4:
            for fam in familias:
                vars_fam = [
                    vars_por_semana[s][fam]
                    for s in semanas_activas
                    if fam in vars_por_semana.get(s, {})
                ]
                if len(vars_fam) < 2:
                    continue
                sum_fam = sum(vars_fam)
                if modo == 'HARD':
                    add_hard(
                        modelo, ctx,
                        modelo.Add(sum_fam <= 1),
                        f"{emp.nombre}_no_rep_{fam}_lt4"
                    )
                else:
                    violacion = modelo.NewIntVar(
                        0, n_activas,
                        f"viol_rep_{fam}_{nombre_safe}_lt4"
                    )
                    modelo.Add(violacion >= sum_fam - 1)
                    ctx.penalizaciones_soft.append(violacion * peso_soft)
            continue

        # ── 3. CASO B: >= 4 semanas activas → solo puede repetir el tipo_inicio ─
        #
        # Para cada familia fam:
        #   - Si v_dict_first[fam] == 1 → fam es el tipo_inicio → puede repetirse
        #   - Si v_dict_first[fam] == 0 → fam NO es el tipo_inicio → max 1 semana
        #
        # Implementación sin OnlyEnforceIf (compatible con add_hard):
        #   sum_fam <= 1 + v_dict_first[fam] * (n_activas - 1)
        #
        #   Cuando v_dict_first[fam]=0: sum_fam <= 1  ✓ (restringe)
        #   Cuando v_dict_first[fam]=1: sum_fam <= n_activas (siempre true) ✓

        first_sem = semanas_activas[0]
        v_dict_first = vars_por_semana.get(first_sem)
        if not v_dict_first:
            continue

        for fam in familias:
            if fam not in v_dict_first:
                continue

            vars_fam = [
                vars_por_semana[s][fam]
                for s in semanas_activas
                if fam in vars_por_semana.get(s, {})
            ]
            if len(vars_fam) < 2:
                continue

            sum_fam = sum(vars_fam)
            # Slack adicional = (n_activas - 1) si fam es tipo_inicio, 0 si no lo es
            slack = v_dict_first[fam] * (n_activas - 1)

            if modo == 'HARD':
                add_hard(
                    modelo, ctx,
                    modelo.Add(sum_fam <= 1 + slack),
                    f"{emp.nombre}_rep_{fam}_inicio"
                )
            else:
                # violacion = max(0, sum_fam - 1 - slack)
                # Cuando fam es tipo_inicio (slack=n_activas-1): violacion siempre 0 ✓
                # Cuando fam no es tipo_inicio (slack=0): violacion >= sum_fam - 1  ✓
                violacion = modelo.NewIntVar(
                    0, n_activas,
                    f"viol_rep_{fam}_{nombre_safe}"
                )
                modelo.Add(violacion >= sum_fam - 1 - slack)
                ctx.penalizaciones_soft.append(violacion * peso_soft)
