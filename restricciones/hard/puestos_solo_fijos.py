"""restricciones/hard/puestos_solo_fijos.py — Regla HARD para restringir asignación de puestos específicos solo a asignaciones fijas."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    # 1. Obtener parámetros globales de la regla para el servicio actual
    params_regla = _re.resolver_parametros_regla(
        'PUESTOS_SOLO_FIJOS', 'GLOBAL', ctx.fecha_inicio,
        ctx.reglas_servicio, {}, {}
    )

    if not _re.regla_existe(params_regla) or _re.regla_suspendida(params_regla):
        return

    # 2. Extraer la lista de puestos restringidos
    if not isinstance(params_regla, dict):
        return
    puestos_restringidos = params_regla.get("puestos", [])
    if not puestos_restringidos or not isinstance(puestos_restringidos, list):
        return

    puestos_set = set(puestos_restringidos)
    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    # 3. Evaluar cada empleado y día del bloque
    for emp in ctx.empleados:
        for dia in range(ctx.dias):
            dia_semana = (dia + ctx.offset_dia) % 7
            fecha_dia_str = (fecha_inicio_dt + timedelta(days=dia)).isoformat()

            # Obtener asignaciones fijas vigentes hoy para este profesional
            params_fijas = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_dia_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal or {}
            )

            # Recopilar los nombres de turnos configurados como fijos para este día
            turnos_fijos_hoy = set()
            if _re.regla_existe(params_fijas) and isinstance(params_fijas, list):
                for asig in params_fijas:
                    fecha_asig = asig.get('Fecha')
                    dia_asig = asig.get('Dia')
                    match = (fecha_asig and fecha_asig == fecha_dia_str) or \
                            (dia_asig and mapa_dias.get(dia_asig) == dia_semana and dia not in ctx.feriados)
                    if match:
                        turno_config = asig['Turno'].replace(" ", "_")
                        turnos_fijos_hoy.add(turno_config)

            # 4. Forzar a 0 las variables de turnos de puestos restringidos que no sean fijos
            for t_nombre, t_info in ctx.turnos_dict.items():
                if t_info.puesto_nombre not in puestos_set:
                    continue

                key = (emp.nombre, dia, t_nombre)
                if key in ctx.turnos:
                    # Validar si el turno coincide con alguna asignación fija de hoy
                    fijado = False
                    for tf in turnos_fijos_hoy:
                        if t_nombre == tf or t_nombre.startswith(tf + "_"):
                            fijado = True
                            break

                    if not fijado:
                        # Forzar la variable a 0 (desactivar el turno para este día y persona)
                        add_hard(
                            modelo, ctx,
                            modelo.Add(ctx.turnos[key] == 0),
                            etiqueta=f"{emp.nombre}_dia{dia}_{t_nombre}"
                        )
