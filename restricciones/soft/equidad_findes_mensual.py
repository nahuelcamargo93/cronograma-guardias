"""
restricciones/soft/equidad_findes_mensual.py — SOFT
Penaliza de forma progresiva la asignación de fines de semana completos y medios trabajados en base al histórico.
Regla: EQUIDAD_FINDES_MENSUAL
"""
from datetime import date, timedelta
import rule_engine as _re
from database.connection import get_connection


def apply(modelo, ctx):
    # 1. Obtener parámetros de la regla
    peso_cfg = ctx.reglas_servicio.get('EQUIDAD_FINDES_MENSUAL', {})
    peso = peso_cfg.get('peso', 500) if isinstance(peso_cfg, dict) else 500
    tipo_regla = peso_cfg.get('tipo', 'MENSUAL').upper() if isinstance(peso_cfg, dict) else 'MENSUAL'
    fecha_inicio_niv_str = peso_cfg.get('fecha_inicio') if isinstance(peso_cfg, dict) else None

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    # 2. Inicializar acumuladores históricos
    completos_historicos = {emp.nombre: 0 for emp in ctx.empleados}
    medios_historicos = {emp.nombre: 0 for emp in ctx.empleados}

    # 3. Cargar históricos si es una regla HISTORICA y hay fecha_inicio
    if tipo_regla == 'HISTORICA' and fecha_inicio_niv_str:
        fecha_fin_hist_dt = fecha_inicio_dt - timedelta(days=1)
        fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()

        if fecha_inicio_niv_str <= fecha_fin_hist_str:
            with get_connection() as conn:
                cronos = conn.execute("""
                    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
                    FROM cronogramas c
                    JOIN guardias g ON c.id = g.cronograma_id
                    JOIN personal p ON g.nombre = p.nombre
                    WHERE p.servicio_id = ?
                      AND c.estado = 'aprobado'
                      AND c.fecha_inicio >= ?
                      AND c.fecha_fin <= ?
                    ORDER BY c.fecha_inicio
                """, (ctx.servicio_id, fecha_inicio_niv_str, fecha_fin_hist_str)).fetchall()

            if cronos:
                crono_ids = [c[0] for c in cronos]
                placeholders = ",".join("?" for _ in crono_ids)
                
                with get_connection() as conn:
                    guardias_hist = conn.execute(f"""
                        SELECT g.nombre, g.fecha, g.cronograma_id
                        FROM guardias g
                        JOIN personal p ON g.nombre = p.nombre
                        WHERE g.cronograma_id IN ({placeholders})
                          AND g.es_finde = 1
                          AND p.servicio_id = ?
                    """, crono_ids + [ctx.servicio_id]).fetchall()

                # Procesar guardias históricas
                guardias_por_finde = {}
                for nom, fecha_str, c_id in guardias_hist:
                    f_dt = date.fromisoformat(fecha_str)
                    wd = f_dt.weekday()
                    if wd in (5, 6):
                        lunes_dt = f_dt - timedelta(days=wd)
                        lunes_str = lunes_dt.isoformat()
                        guardias_por_finde.setdefault(nom, {}).setdefault((c_id, lunes_str), set()).add(wd)

                # Calcular completos y medios históricos reales
                for nom, findes_dict in guardias_por_finde.items():
                    c_count = 0
                    m_count = 0
                    for (c_id, lunes_str), wds in findes_dict.items():
                        if len(wds) >= 2:
                            c_count += 1
                        elif len(wds) == 1:
                            m_count += 1
                    if nom in completos_historicos:
                        completos_historicos[nom] = c_count
                    if nom in medios_historicos:
                        medios_historicos[nom] = m_count

    # 4. Agrupar semanas del cronograma actual
    dias_por_semana = {}
    for d in range(ctx.dias):
        lunes = (fecha_inicio_dt + timedelta(days=d))
        lunes = lunes - timedelta(days=lunes.weekday())
        dias_por_semana.setdefault(lunes.isoformat(), []).append(d)

    # 5. Modelar en OR-Tools
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'EQUIDAD_FINDES_MENSUAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        completos_trab = []
        medios_trab = []

        for sem_key, dias_sem in dias_por_semana.items():
            sem_id = sem_key.replace('-', '_')
            sabados = [d for d in dias_sem if (d + ctx.offset_dia) % 7 == 5]
            domingos = [d for d in dias_sem if (d + ctx.offset_dia) % 7 == 6]
            if not sabados or not domingos:
                continue
            s, dom = sabados[0], domingos[0]

            t_f_names = ctx.demanda_turnos.get('Finde_Feriado', {}).keys()

            pool_sat = [ctx.turnos[(emp.nombre, s, t)] for t in t_f_names if (emp.nombre, s, t) in ctx.turnos]
            v_sat = modelo.NewBoolVar(f'sat_{emp.nombre}_{sem_id}')
            if pool_sat:
                modelo.AddMaxEquality(v_sat, pool_sat)
            else:
                modelo.Add(v_sat == 0)

            pool_sun = [ctx.turnos[(emp.nombre, dom, t)] for t in t_f_names if (emp.nombre, dom, t) in ctx.turnos]
            v_sun = modelo.NewBoolVar(f'sun_{emp.nombre}_{sem_id}')
            if pool_sun:
                modelo.AddMaxEquality(v_sun, pool_sun)
            else:
                modelo.Add(v_sun == 0)

            v_comp = modelo.NewBoolVar(f'f_comp_{emp.nombre}_{sem_id}')
            modelo.AddBoolAnd([v_sat, v_sun]).OnlyEnforceIf(v_comp)
            modelo.AddBoolOr([v_sat.Not(), v_sun.Not()]).OnlyEnforceIf(v_comp.Not())

            v_med = modelo.NewBoolVar(f'f_med_{emp.nombre}_{sem_id}')
            modelo.Add(v_sat + v_sun - 2 * v_comp == v_med)

            completos_trab.append(v_comp)
            medios_trab.append(v_med)

        hist_c = completos_historicos.get(emp.nombre, 0)
        hist_m = medios_historicos.get(emp.nombre, 0)

        # Penalización progresiva independientes para completos
        if completos_trab:
            N_comp = len(completos_trab)
            at_least_comp = [modelo.NewBoolVar(f'at_least_comp_{emp.nombre}_{j}') for j in range(1, N_comp + 1)]
            modelo.Add(sum(completos_trab) == sum(at_least_comp))
            for j in range(N_comp - 1):
                modelo.Add(at_least_comp[j] >= at_least_comp[j + 1])
            for j, var in enumerate(at_least_comp):
                ctx.penalizaciones_soft.append(var * (hist_c + j + 1) * peso)

        # Penalización progresiva independientes para medios
        if medios_trab:
            N_med = len(medios_trab)
            at_least_med = [modelo.NewBoolVar(f'at_least_med_{emp.nombre}_{j}') for j in range(1, N_med + 1)]
            modelo.Add(sum(medios_trab) == sum(at_least_med))
            for j in range(N_med - 1):
                modelo.Add(at_least_med[j] >= at_least_med[j + 1])
            for j, var in enumerate(at_least_med):
                ctx.penalizaciones_soft.append(var * (hist_m + j + 1) * peso)
