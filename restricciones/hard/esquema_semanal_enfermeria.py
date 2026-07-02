"""restricciones/hard/esquema_semanal_enfermeria.py — Esquema semanal fijo para Enfermería Servicio 2.

Trabajan exactamente 4 turnos de 6 hs y 1 guardia de 12 hs si la semana está activa.
Esto deja automáticamente 2 francos en la semana.

Semana cortada (inicio o fin de mes): si la semana tiene menos de
`min_dias_semana_completa` días hábiles (lun-vie, default 3), la restricción
pasa a modo SOFT para evitar infeasibility. El mes adyacente completa con
HARD vía historial.

NOTA: Los feriados que caen en día de semana (lun-vie) cuentan como día hábil
para esta regla, ya que se pueden asignar turnos de 12 hs en feriados.
Si esto cambia (se prohíben turnos de 12 hs en feriados), hay que ajustar
la lógica de conteo de días hábiles.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario


def apply(modelo, ctx) -> None:
    if 'ESQUEMA_SEMANAL_ENFERMERIA' not in ctx.reglas_servicio:
        return

    params = ctx.reglas_servicio['ESQUEMA_SEMANAL_ENFERMERIA']
    excluidos = params.get('excluidos', [])
    modo = params.get('modo', 'HARD').upper()
    peso_soft = params.get('peso_soft', 10000)
    
    # Parámetros dinámicos de turnos y cantidad
    turnos_objetivo = params.get('turnos', ['MT', 'TNN'])
    cantidad = params.get('cantidad', 1)
    min_dias_completa = params.get('min_dias_semana_completa', 3)

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
    historial = ctx.historial_semana_previa or {}



    for emp in ctx.empleados:
        if emp.nombre in excluidos:
            continue

        hist_emp = historial.get(emp.nombre, [])

        for (iso_y, iso_w), days in semanas.items():
            fl = days[0][1]
            fecha_lunes = (fl - timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
            
            # Contar licencias del bloque actual en esta semana
            licencias_en_bloque = sum(1 for d, _ in days if d in emp.dias_licencia)
            if licencias_en_bloque == len(days):
                # Si tiene toda la semana activa de licencia, no forzamos el esquema rígido
                continue

            # Contar guardias previas de esta misma semana calendario en el mes anterior
            prev_sem = [h for h in hist_emp
                        if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_y, iso_w)]
            prev_turnos_12h = sum(1 for h in prev_sem if h['turno'] in turnos_objetivo)

            # Obtener variables de categoría semanal
            v_dict = ctx.vars_turno_sem.get((emp.nombre, fecha_lunes))
            if not v_dict:
                continue

            # La variable Activa indica si el empleado tiene asignada alguna categoría semanal
            activa = modelo.NewBoolVar(f"activa_{emp.nombre}_{iso_y}w{iso_w}")
            modelo.Add(activa == sum(v_dict.values()))

            # Sumar variables de turnos del grupo objetivo (ej: de 12 horas)
            vars_turnos = [
                ctx.turnos[(emp.nombre, d, t)]
                for d, _ in days
                for t in turnos_objetivo
                if (emp.nombre, d, t) in ctx.turnos
            ]

            if vars_turnos or prev_turnos_12h > 0:
                # Semana cortada: forzar SOFT si pocos días hábiles (lun-vie)
                dias_habiles = sum(1 for _, fecha in days if fecha.weekday() < 5)
                modo_efectivo = modo
                if dias_habiles < min_dias_completa:
                    modo_efectivo = "SOFT"

                if modo_efectivo == "HARD":
                    add_hard(modelo, ctx,
                             modelo.Add(sum(vars_turnos) + prev_turnos_12h == cantidad * activa),
                             f"{emp.nombre}_w{iso_w}_cant_{'_'.join(turnos_objetivo)}")
                else:
                    # Modo SOFT: penalizar desviaciones con variables enteras de holgura
                    v_over = modelo.NewIntVar(0, 7, f"viol_over_{emp.nombre}_{iso_y}w{iso_w}")
                    v_under = modelo.NewIntVar(0, cantidad, f"viol_under_{emp.nombre}_{iso_y}w{iso_w}")
                    modelo.Add(sum(vars_turnos) + prev_turnos_12h + v_under - v_over == cantidad * activa)
                    ctx.penalizaciones_soft.append((v_over + v_under) * peso_soft)
