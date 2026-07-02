"""restricciones/hard/semanas_seguimiento_requeridas.py — Mínimo de semanas de seguimiento de mañana, tarde y total por mes."""
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

    semana_turnos = ctx.demanda_turnos.get('Semana', {}).keys()
    
    # Filtrar los turnos de mañana y tarde, excluyendo 'especial'
    turnos_m = [t for t in semana_turnos if t.startswith('Mañana') and 'especial' not in t.lower()]
    turnos_t = [t for t in semana_turnos if t.startswith('Tarde') and 'especial' not in t.lower()]

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'SEMANAS_SEGUIMIENTO_REQUERIDAS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
            
        if not isinstance(params, dict):
            continue

        # Función para verificar disponibilidad del día (no es licencia y no tiene franco forzado,
        # a menos que el franco forzado sea anulado por una asignación fija por fecha)
        def _disponible(d_idx):
            if d_idx in emp.dias_licencia:
                return False
            fecha_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = _re.regla_existe(p) and not _re.regla_suspendida(p)

            tiene_fija_fecha = False
            params_fija = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                for asig in params_fija:
                    if asig.get('Fecha') == fecha_str:
                        tiene_fija_fecha = True
                        break

            if tiene_franco and not tiene_fija_fecha:
                return False
            return True

        # Calcular semanas disponibles
        semanas_disponibles = 0
        for sem_key, dias_sem in dias_por_semana.items():
            lv = [d for d in dias_sem if (d + ctx.offset_dia) % 7 < 5]
            lv_disp = [d for d in lv if _disponible(d)]
            if len(lv_disp) >= 4:
                semanas_disponibles += 1

        # Cargar parámetros desde por_disponibilidad
        if 'por_disponibilidad' not in params:
            raise ValueError(
                f"La regla SEMANAS_SEGUIMIENTO_REQUERIDAS para el empleado '{emp.nombre}' "
                f"en la fecha {ctx.fecha_inicio} no tiene configurado 'por_disponibilidad'."
            )

        por_disp = params.get('por_disponibilidad', {})
        k_disp_str = str(semanas_disponibles)
        if k_disp_str not in por_disp:
            raise ValueError(
                f"La regla SEMANAS_SEGUIMIENTO_REQUERIDAS para el empleado '{emp.nombre}' "
                f"en la fecha {ctx.fecha_inicio} no tiene configuración en 'por_disponibilidad' "
                f"para {k_disp_str} semanas disponibles."
            )

        conf_disp = por_disp[k_disp_str]
        min_manana = conf_disp.get('min_manana', 0)
        min_tarde = conf_disp.get('min_tarde', 0)
        min_total = conf_disp.get('min_total', 0)

        if min_manana <= 0 and min_tarde <= 0 and min_total <= 0:
            continue

        semanas_m = []
        semanas_t = []
        semanas_cualquiera = []

        for sem_key, dias_sem in dias_por_semana.items():
            sem_id = sem_key.replace('-', '_')
            # Días de lunes a viernes
            lv = [d for d in dias_sem if (d + ctx.offset_dia) % 7 < 5]
            lv_disp = [d for d in lv if _disponible(d)]
            
            if len(lv_disp) < 4:
                continue

            # --- Mañana ---
            cumple_m_list = []
            for t in turnos_m:
                t_dia = None
                if t.startswith('Mañana_'):
                    suffix = t.replace('Mañana_', '')
                    t_dia = f"Dia_{suffix}"
                elif t.startswith('Mañana'):
                    suffix = t.replace('Mañana', '')
                    t_dia = f"Dia_{suffix}"

                vars_m_t = []
                for d in lv_disp:
                    if (emp.nombre, d, t) in ctx.turnos:
                        vars_m_t.append(ctx.turnos[(emp.nombre, d, t)])
                    if t_dia and (emp.nombre, d, t_dia) in ctx.turnos:
                        vars_m_t.append(ctx.turnos[(emp.nombre, d, t_dia)])
                
                if len(vars_m_t) >= 4:
                    cumple_m_t = modelo.NewBoolVar(f'cumple_seg_{t}_{emp.nombre}_{sem_id}')
                    modelo.Add(sum(vars_m_t) >= 4).OnlyEnforceIf(cumple_m_t)
                    modelo.Add(sum(vars_m_t) < 4).OnlyEnforceIf(cumple_m_t.Not())
                    cumple_m_list.append(cumple_m_t)
            
            cumple_m = modelo.NewBoolVar(f'cumple_seg_m_{emp.nombre}_{sem_id}')
            if cumple_m_list:
                modelo.AddMaxEquality(cumple_m, cumple_m_list)
            else:
                modelo.Add(cumple_m == 0)
            semanas_m.append(cumple_m)

            # --- Tarde ---
            cumple_t_list = []
            for t in turnos_t:
                t_dia = None
                if t.startswith('Tarde_'):
                    suffix = t.replace('Tarde_', '')
                    t_dia = f"Dia_{suffix}"
                elif t.startswith('Tarde'):
                    suffix = t.replace('Tarde', '')
                    t_dia = f"Dia_{suffix}"

                vars_t_t = []
                for d in lv_disp:
                    if (emp.nombre, d, t) in ctx.turnos:
                        vars_t_t.append(ctx.turnos[(emp.nombre, d, t)])
                    if t_dia and (emp.nombre, d, t_dia) in ctx.turnos:
                        vars_t_t.append(ctx.turnos[(emp.nombre, d, t_dia)])
                
                if len(vars_t_t) >= 4:
                    cumple_t_t = modelo.NewBoolVar(f'cumple_seg_{t}_{emp.nombre}_{sem_id}')
                    modelo.Add(sum(vars_t_t) >= 4).OnlyEnforceIf(cumple_t_t)
                    modelo.Add(sum(vars_t_t) < 4).OnlyEnforceIf(cumple_t_t.Not())
                    cumple_t_list.append(cumple_t_t)
            
            cumple_t = modelo.NewBoolVar(f'cumple_seg_t_{emp.nombre}_{sem_id}')
            if cumple_t_list:
                modelo.AddMaxEquality(cumple_t, cumple_t_list)
            else:
                modelo.Add(cumple_t == 0)
            semanas_t.append(cumple_t)

            # --- Cualquiera ---
            cumple_cualquiera = modelo.NewBoolVar(f'cumple_seg_cualquiera_{emp.nombre}_{sem_id}')
            modelo.AddMaxEquality(cumple_cualquiera, [cumple_m, cumple_t])
            semanas_cualquiera.append(cumple_cualquiera)

        # Restricciones del mes
        if min_manana > 0 and semanas_m:
            efectivo_m = min(min_manana, len(semanas_m))
            add_hard(modelo, ctx,
                     modelo.Add(sum(semanas_m) >= efectivo_m),
                     f"{emp.nombre}_min_seg_m")

        if min_tarde > 0 and semanas_t:
            efectivo_t = min(min_tarde, len(semanas_t))
            add_hard(modelo, ctx,
                     modelo.Add(sum(semanas_t) >= efectivo_t),
                     f"{emp.nombre}_min_seg_t")

        if min_total > 0 and semanas_cualquiera:
            efectivo_tot = min(min_total, len(semanas_cualquiera))
            add_hard(modelo, ctx,
                     modelo.Add(sum(semanas_cualquiera) >= efectivo_tot),
                     f"{emp.nombre}_min_seg_tot")
