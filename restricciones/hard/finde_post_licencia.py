"""restricciones/hard/finde_post_licencia.py — Obliga a trabajar el primer fin de semana tras retornar de una licencia.

Si una persona tiene algún tipo de licencia, al retornar de ella,
el primer fin de semana disponible en el mes debe ser trabajado
según la configuración establecida en los parámetros de la regla:
- "completo": Trabaja obligatoriamente sábado y domingo.
- "medio": Trabaja al menos un día (sábado o domingo).
- "null": Sin restricciones adicionales (desactivada).
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'FINDE_POST_LICENCIA', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        configuracion = params.get('configuracion')
        if configuracion not in ("completo", "medio"):
            continue

        # 1. Agrupar sábados y domingos en fines de semana del mes
        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, {})
                if wd == 5:
                    findes[lunes]['sat'] = d
                elif wd == 6:
                    findes[lunes]['sun'] = d

        findes_ordenados = sorted(findes.items(), key=lambda x: x[0])

        # Función de disponibilidad para evitar colisiones
        def esta_disponible(d):
            if d in emp.dias_licencia:
                return False
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            return not (_re.regla_existe(p) and not _re.regla_suspendida(p))

        # 2. Identificar cuándo el empleado retorna de una licencia
        dias_vuelta = []
        for d in sorted(emp.dias_licencia):
            d_vuelta = d + 1
            if d_vuelta < ctx.dias and d_vuelta not in emp.dias_licencia:
                dias_vuelta.append(d_vuelta)

        # 3. Para cada vuelta de licencia, buscar su primer fin de semana posterior
        # y aplicar la restricción.
        for d_vuelta in dias_vuelta:
            finde_objetivo = None
            for lunes_iso, dias_f in findes_ordenados:
                d_sat = dias_f.get('sat')
                d_sun = dias_f.get('sun')
                
                # Un fin de semana es posterior si al menos uno de sus días lo es
                es_posterior = False
                if d_sat is not None and d_sat >= d_vuelta:
                    es_posterior = True
                if d_sun is not None and d_sun >= d_vuelta:
                    es_posterior = True

                if es_posterior:
                    finde_objetivo = (lunes_iso, d_sat, d_sun)
                    break

            if finde_objetivo:
                lunes_iso, d_sat, d_sun = finde_objetivo
                
                # Crear variables de decisión si trabaja el sábado/domingo correspondiente
                v_sat = None
                if d_sat is not None:
                    pool_sat = [ctx.turnos[(emp.nombre, d_sat, t)]
                                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                                if (emp.nombre, d_sat, t) in ctx.turnos]
                    if pool_sat:
                        v_sat = modelo.NewBoolVar(f'post_lic_sat_{emp.nombre}_{lunes_iso}')
                        modelo.AddMaxEquality(v_sat, pool_sat)

                v_sun = None
                if d_sun is not None:
                    pool_sun = [ctx.turnos[(emp.nombre, d_sun, t)]
                                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                                if (emp.nombre, d_sun, t) in ctx.turnos]
                    if pool_sun:
                        v_sun = modelo.NewBoolVar(f'post_lic_sun_{emp.nombre}_{lunes_iso}')
                        modelo.AddMaxEquality(v_sun, pool_sun)

                # Filtrar qué días están libres de licencias y francos forzados
                vars_disponibles = []
                if v_sat is not None and esta_disponible(d_sat):
                    vars_disponibles.append(v_sat)
                if v_sun is not None and esta_disponible(d_sun):
                    vars_disponibles.append(v_sun)

                # Aplicar restricciones según configuración
                if configuracion == "completo":
                    for v in vars_disponibles:
                        add_hard(modelo, ctx, modelo.Add(v == 1), f"{emp.nombre}_post_lic_{v.Name()}")
                elif configuracion == "medio":
                    if len(vars_disponibles) == 2:
                        add_hard(modelo, ctx, modelo.Add(sum(vars_disponibles) >= 1), f"{emp.nombre}_post_lic_medio_{lunes_iso}")
                    elif len(vars_disponibles) == 1:
                        add_hard(modelo, ctx, modelo.Add(vars_disponibles[0] == 1), f"{emp.nombre}_post_lic_medio_unico_{lunes_iso}")
