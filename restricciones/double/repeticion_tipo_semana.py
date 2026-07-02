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
    n_semanas = len(semanas_keys)
    if n_semanas < 5:
        return  # Solo aplica para meses con 5 o 6 semanas planificadas

    for emp in ctx.empleados:
        nombre_safe = emp.nombre.replace(' ', '_').replace(',', '').replace('-', '_')

        # Alineación de Semana 5 con Semana 1 (índices 4 y 0)
        if n_semanas >= 5:
            sem_1 = semanas_keys[0]
            sem_5 = semanas_keys[4]

            v_dict_1 = ctx.vars_turno_sem.get((emp.nombre, sem_1))
            v_dict_5 = ctx.vars_turno_sem.get((emp.nombre, sem_5))

            if v_dict_1 and v_dict_5:
                # La semana está activa si tiene asignada alguna categoría semanal
                activa_1 = modelo.NewBoolVar(f"act_w1_{nombre_safe}")
                activa_5 = modelo.NewBoolVar(f"act_w5_{nombre_safe}")
                modelo.Add(activa_1 == sum(v_dict_1.values()))
                modelo.Add(activa_5 == sum(v_dict_5.values()))

                for fam in familias:
                    if fam in v_dict_1 and fam in v_dict_5:
                        if modo == 'HARD':
                            add_hard(
                                modelo, ctx,
                                modelo.Add(v_dict_5[fam] == v_dict_1[fam]).OnlyEnforceIf([activa_1, activa_5]),
                                f"{emp.nombre}_align_w5_w1_{fam}"
                            )
                        else:
                            viol = modelo.NewBoolVar(f"viol_align_w5_w1_{fam}_{nombre_safe}")
                            modelo.Add(v_dict_5[fam] == v_dict_1[fam]).OnlyEnforceIf([activa_1, activa_5, viol.Not()])
                            ctx.penalizaciones_soft.append(viol * peso_soft)

        # Alineación de Semana 6 con Semana 2 (índices 5 y 1)
        if n_semanas >= 6:
            sem_2 = semanas_keys[1]
            sem_6 = semanas_keys[5]

            v_dict_2 = ctx.vars_turno_sem.get((emp.nombre, sem_2))
            v_dict_6 = ctx.vars_turno_sem.get((emp.nombre, sem_6))

            if v_dict_2 and v_dict_6:
                activa_2 = modelo.NewBoolVar(f"act_w2_{nombre_safe}")
                activa_6 = modelo.NewBoolVar(f"act_w6_{nombre_safe}")
                modelo.Add(activa_2 == sum(v_dict_2.values()))
                modelo.Add(activa_6 == sum(v_dict_6.values()))

                for fam in familias:
                    if fam in v_dict_2 and fam in v_dict_6:
                        if modo == 'HARD':
                            add_hard(
                                modelo, ctx,
                                modelo.Add(v_dict_6[fam] == v_dict_2[fam]).OnlyEnforceIf([activa_2, activa_6]),
                                f"{emp.nombre}_align_w6_w2_{fam}"
                            )
                        else:
                            viol = modelo.NewBoolVar(f"viol_align_w6_w2_{fam}_{nombre_safe}")
                            modelo.Add(v_dict_6[fam] == v_dict_2[fam]).OnlyEnforceIf([activa_2, activa_6, viol.Not()])
                            ctx.penalizaciones_soft.append(viol * peso_soft)
