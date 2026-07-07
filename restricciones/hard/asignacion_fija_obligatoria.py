"""restricciones/hard/asignacion_fija_obligatoria.py — Fuerza la asignación fija como obligatoria.

Si un profesional tiene una ASIGNACION_FIJA configurada:
- Por fecha específica: se fuerza incondicionalmente (prevalece sobre FRANCO_FORZADO).
- Recurrente (por día de semana): se fuerza salvo que haya FRANCO_FORZADO ese día.

En ambos casos, los días de licencia se exceptúan para evitar inviabilidad.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re

_MAPA_DIAS = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
              "Viernes": 4, "Sabado": 5, "Domingo": 6}


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    for emp in ctx.empleados:
        for d in range(ctx.dias):
            # Licencia: no forzar nada
            if d in emp.dias_licencia:
                continue

            dia_semana = (d + ctx.offset_dia) % 7
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            td = "Finde_Feriado" if (dia_semana >= 5 or d in ctx.feriados) else "Semana"

            params = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue

            # Resolver franco forzado una sola vez por día
            params_franco = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = (_re.regla_existe(params_franco)
                            and not _re.regla_suspendida(params_franco))

            for asig in params:
                fecha_asig = asig.get('Fecha')
                dia_asig = asig.get('Dia')
                turno_fijo = asig.get('Turno', '').replace(" ", "_")
                if not turno_fijo:
                    continue

                es_por_fecha = bool(fecha_asig and fecha_asig == fecha_d_str)
                es_por_dia = bool(dia_asig
                                  and _MAPA_DIAS.get(dia_asig) == dia_semana
                                  and d not in ctx.feriados)

                # Determinar si se debe forzar
                forzar = False
                if es_por_fecha:
                    # Por fecha: siempre obligatoria (prevalece sobre franco forzado)
                    forzar = True
                elif es_por_dia:
                    # Recurrente: obligatoria salvo franco forzado
                    if not tiene_franco:
                        forzar = True

                if not forzar:
                    continue

                # Buscar la variable del turno y forzar == 1
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    key = (emp.nombre, d, t)
                    if key in ctx.turnos and (t == turno_fijo
                                              or t.startswith(turno_fijo + "_")):
                        add_hard(modelo, ctx,
                                 modelo.Add(ctx.turnos[key] == 1),
                                 f"fija_oblig_{emp.nombre}_d{d}_{t}")
                        break

