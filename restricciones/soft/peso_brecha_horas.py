"""
restricciones/soft/peso_brecha_horas.py — SOFT
Nivelación incremental de horas asignadas en base a la disponibilidad (días hábiles libres de licencias).
Regla: PESO_BRECHA_HORAS
"""
from datetime import date, timedelta
import rule_engine as _re
from database.connection import get_connection

def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    # 1. Obtener la regla y ver si está activa
    regla_serv = ctx.reglas_servicio.get('PESO_BRECHA_HORAS')
    if not regla_serv:
        tiene_regla = False
        for emp in ctx.empleados:
            params = _re.resolver_parametros_regla(
                'PESO_BRECHA_HORAS', emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_suspendida(params):
                tiene_regla = True
                break
        if not tiene_regla:
            return
        regla_serv = {}

    peso_global = regla_serv.get('peso', 20) if isinstance(regla_serv, dict) else 20
    fecha_inicio_niv_str = regla_serv.get('fecha_inicio') if isinstance(regla_serv, dict) else None

    # Por defecto, nivelación desde el 1 de enero del año actual
    if not fecha_inicio_niv_str:
        fecha_inicio_niv_str = f"{fecha_inicio_dt.year}-01-01"

    fecha_fin_hist_dt = fecha_inicio_dt - timedelta(days=1)
    fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()

    horas_historicas = {emp.nombre: 0.0 for emp in ctx.empleados}
    dias_disponibles_historicos = {emp.nombre: 0.0 for emp in ctx.empleados}

    # 2. Si la fecha de inicio del histórico es menor o igual al día anterior a la planificación, consultar historial
    if fecha_inicio_niv_str <= fecha_fin_hist_str:
        with get_connection() as conn:
            # Obtener cronogramas aprobados del servicio en el rango histórico
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
            emp_nombres = [emp.nombre for emp in ctx.empleados]
            emp_placeholders = ",".join("?" for _ in emp_nombres)

            with get_connection() as conn:
                # Suma de horas en el período histórico
                horas_rows = conn.execute(f"""
                    SELECT g.nombre, SUM(g.horas)
                    FROM guardias g
                    JOIN personal p ON g.nombre = p.nombre
                    WHERE g.cronograma_id IN ({placeholders})
                      AND p.servicio_id = ?
                    GROUP BY g.nombre
                """, crono_ids + [ctx.servicio_id]).fetchall()

                # Licencias en el período histórico
                licencias_rows = conn.execute(f"""
                    SELECT nombre, fecha_inicio, fecha_fin
                    FROM licencias
                    WHERE nombre IN ({emp_placeholders})
                      AND fecha_inicio <= ? AND fecha_fin >= ?
                      AND COALESCE(activa, 1) = 1
                """, emp_nombres + [fecha_fin_hist_str, fecha_inicio_niv_str]).fetchall()

            # Mapear horas
            for nom, h_sum in horas_rows:
                if nom in horas_historicas:
                    horas_historicas[nom] = float(h_sum or 0.0)

            # Mapear licencias históricas (generar conjunto de fechas por empleado)
            licencias_por_emp = {emp.nombre: set() for emp in ctx.empleados}
            for nom, f_ini, f_fin in licencias_rows:
                if nom in licencias_por_emp:
                    # Rango de fechas de la licencia
                    curr_dt = date.fromisoformat(f_ini)
                    fin_dt = date.fromisoformat(f_fin)
                    while curr_dt <= fin_dt:
                        licencias_por_emp[nom].add(curr_dt.isoformat())
                        curr_dt += timedelta(days=1)

            # Calcular días disponibles en el rango histórico
            for emp in ctx.empleados:
                start_hist_str = max(fecha_inicio_niv_str, emp.fecha_inicio_historial) if emp.fecha_inicio_historial else fecha_inicio_niv_str
                if start_hist_str > fecha_fin_hist_str:
                    continue

                curr_dt = date.fromisoformat(start_hist_str)
                cnt_dias = 0
                while curr_dt <= fecha_fin_hist_dt:
                    date_str = curr_dt.isoformat()
                    # Si no estuvo de licencia ese día
                    if date_str not in licencias_por_emp[emp.nombre]:
                        cnt_dias += 1
                    curr_dt += timedelta(days=1)
                
                dias_disponibles_historicos[emp.nombre] = float(cnt_dias)

    # 3. Calcular el piso mínimo del ratio histórico (Floor) entre empleados activos en la regla con historial válido
    ratios_historicos = {}
    empleados_activos_regla = []
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_HORAS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params):
            empleados_activos_regla.append(emp.nombre)
            d_hist = dias_disponibles_historicos[emp.nombre]
            if d_hist > 0:
                ratios_historicos[emp.nombre] = horas_historicas[emp.nombre] / d_hist
            else:
                ratios_historicos[emp.nombre] = 0.0

    ratios_para_floor = [ratios_historicos[nom] for nom in empleados_activos_regla if dias_disponibles_historicos[nom] > 0]
    floor_ratio = min(ratios_para_floor) if ratios_para_floor else 0.0

    # 4. Modelar en CP-SAT para el bloque actual
    limite = ctx.reglas_servicio.get('LIMITES_SOFT_RULES', {}).get('MAX_HORAS_LIMITE_BASE', 200)

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_HORAS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        peso_emp = params.get('peso', peso_global) if isinstance(params, dict) else peso_global

        # Calcular días disponibles en el bloque actual
        dias_disponibles_actual = float(ctx.dias - len(emp.dias_licencia))
        d_total = dias_disponibles_historicos[emp.nombre] + dias_disponibles_actual

        if d_total <= 0:
            continue

        # Recopilar variables de decisión de horas en el mes
        horas_vars = []
        for d in range(ctx.dias):
            dia_semana = (d + ctx.offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (d in ctx.feriados)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            
            for t in ctx.demanda_turnos.get(tipo_dia, {}).keys():
                if (emp.nombre, d, t) in ctx.turnos:
                    duracion = ctx.turnos_dict[t].horas
                    horas_vars.append(ctx.turnos[(emp.nombre, d, t)] * duracion)

        if horas_vars:
            total_horas_var = modelo.NewIntVar(0, limite, f'total_horas_brecha_{emp.nombre}')
            modelo.Add(total_horas_var == sum(horas_vars))

            # Crear variables booleanas ordenadas para cada hora potencial
            at_least_horas = [modelo.NewBoolVar(f'at_least_horas_{emp.nombre}_{j}') for j in range(1, limite + 1)]
            modelo.Add(total_horas_var == sum(at_least_horas))
            for j in range(limite - 1):
                modelo.Add(at_least_horas[j] >= at_least_horas[j + 1])

            # Penalizar de forma incremental hora a hora en base al incremento del ratio
            h_hist = horas_historicas[emp.nombre]
            for j in range(1, limite + 1):
                # Ratio resultante si llega a la hora j
                ratio_j = (h_hist + j) / d_total
                ratio_rel_j = max(0.0, ratio_j - floor_ratio)
                coef = int(round(ratio_rel_j * peso_emp))
                
                if coef > 0:
                    ctx.penalizaciones_soft.append(at_least_horas[j - 1] * coef)
