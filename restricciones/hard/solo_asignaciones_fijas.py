"""restricciones/hard/solo_asignaciones_fijas.py — Limita al profesional a cubrir únicamente asignaciones fijas."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re

def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    for emp in ctx.empleados:
        ref = ctx.fecha_inicio
        # Verificar si la regla SOLO_ASIGNACIONES_FIJAS aplica a este profesional
        params_saf = _re.resolver_parametros_regla(
            'SOLO_ASIGNACIONES_FIJAS', emp.nombre, ref,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params_saf):
            continue

        # Si está activa, para cada día del mes bloqueamos todo lo que no sea una asignación fija
        for dia in range(ctx.dias):
            fecha_dia_str = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
            dia_semana = (dia + ctx.offset_dia) % 7
            
            # Resolver asignaciones fijas del empleado para este día
            params_fija = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_dia_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            # Determinar qué turnos específicos están fijos hoy
            turnos_fijos = set()
            if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                for asig in params_fija:
                    fecha_asig = asig.get('Fecha')
                    dia_asig   = asig.get('Dia')
                    match = (fecha_asig and fecha_asig == fecha_dia_str) or \
                            (dia_asig and mapa_dias.get(dia_asig) == dia_semana and dia not in ctx.feriados)
                    if match:
                        turno_config = asig['Turno'].replace(" ", "_")
                        turnos_fijos.add(turno_config)
            
            # Forzar a 0 todos los turnos que no correspondan a una asignación fija
            for td in ("Semana", "Finde_Feriado"):
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, dia, t) in ctx.turnos:
                        is_fixed = False
                        for tf in turnos_fijos:
                            if t == tf or t.startswith(tf + "_"):
                                is_fixed = True
                                break
                        if not is_fixed:
                            # Forzar variable del turno a 0
                            add_hard(modelo, ctx,
                                     modelo.Add(ctx.turnos[(emp.nombre, dia, t)] == 0),
                                     f"{emp.nombre}_dia{dia}_{t}_saf")
