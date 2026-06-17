"""
restricciones/soft/peso_brecha_turno.py — SOFT
Nivelación de turnos asignados por profesional con soporte para nivelación histórica, nivelación relativa, turno configurable y peso por empleado.
Regla: PESO_BRECHA_TURNO
"""
from datetime import date, timedelta
import rule_engine as _re
from database.connection import get_connection
import json

def es_turno_objetivo(turno_nombre, objetivo):
    return turno_nombre.startswith(objetivo) or objetivo in turno_nombre

def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    
    # 1. Obtener la regla y ver si está activa
    regla_serv = ctx.reglas_servicio.get('PESO_BRECHA_TURNO')
    if not regla_serv:
        tiene_regla = False
        for emp in ctx.empleados:
            params = _re.resolver_parametros_regla(
                'PESO_BRECHA_TURNO', emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_suspendida(params):
                tiene_regla = True
                break
        if not tiene_regla:
            return
        regla_serv = {}

    # Validar parámetro 'turno' obligatorio en servicio o empleados
    turno_objetivo = None
    if isinstance(regla_serv, dict) and 'turno' in regla_serv:
        turno_objetivo = regla_serv['turno']

    if not turno_objetivo:
        for emp in ctx.empleados:
            params = _re.resolver_parametros_regla(
                'PESO_BRECHA_TURNO', emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_suspendida(params) and isinstance(params, dict) and 'turno' in params:
                turno_objetivo = params['turno']
                break

    if not turno_objetivo:
        raise ValueError("Falta configurar el parámetro 'turno' en la regla PESO_BRECHA_TURNO")

    nivelacion_config = regla_serv.get('nivelacion_historica') if isinstance(regla_serv, dict) else None
    turnos_historicos = {emp.nombre: 0.0 for emp in ctx.empleados}
    dias_disponibles_historicos = {emp.nombre: 0.0 for emp in ctx.empleados}

    # 2. Si la nivelación histórica está activa, calcular históricos reales y virtuales
    if nivelacion_config and nivelacion_config.get('activo'):
        tipo_niv = nivelacion_config.get('tipo', 'ANUAL').upper()
        fecha_inicio_niv_str = nivelacion_config.get('fecha_inicio')
        
        if not fecha_inicio_niv_str:
            if tipo_niv == 'ANUAL':
                fecha_inicio_niv_str = f"{fecha_inicio_dt.year}-01-01"
            else:
                fecha_inicio_niv_str = None
                
        if fecha_inicio_niv_str:
            fecha_fin_hist_dt = fecha_inicio_dt - timedelta(days=1)
            fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()
            
            if fecha_inicio_niv_str <= fecha_fin_hist_str:
                with get_connection() as conn:
                    # Obtener todos los cronogramas aprobados del servicio en el rango de nivelación
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
                        # Guardias históricas de esos cronogramas
                        guardias_hist = conn.execute(f"""
                            SELECT g.nombre, g.fecha, g.turno, g.cronograma_id
                            FROM guardias g
                            JOIN personal p ON g.nombre = p.nombre
                            WHERE g.cronograma_id IN ({placeholders})
                              AND p.servicio_id = ?
                        """, crono_ids + [ctx.servicio_id]).fetchall()
                        
                        # Licencias en el período histórico
                        licencias_rows = conn.execute(f"""
                            SELECT nombre, fecha_inicio, fecha_fin
                            FROM licencias
                            WHERE nombre IN ({emp_placeholders})
                              AND fecha_inicio <= ? AND fecha_fin >= ?
                              AND COALESCE(activa, 1) = 1
                        """, emp_nombres + [fecha_fin_hist_str, fecha_inicio_niv_str]).fetchall()
                        
                    # Mapear licencias históricas
                    licencias_por_emp = {emp.nombre: set() for emp in ctx.empleados}
                    for nom, f_ini, f_fin in licencias_rows:
                        if nom in licencias_por_emp:
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
                            if date_str not in licencias_por_emp[emp.nombre]:
                                cnt_dias += 1
                            curr_dt += timedelta(days=1)
                        dias_disponibles_historicos[emp.nombre] = float(cnt_dias)
                    
                    guardias_by_emp_crono = {} # {(crono_id, nombre): turnos_trabajados}
                    for nom, _, t_nom, c_id in guardias_hist:
                        if es_turno_objetivo(t_nom, turno_objetivo):
                            guardias_by_emp_crono[(c_id, nom)] = guardias_by_emp_crono.get((c_id, nom), 0) + 1
                    
                    # Para cada cronograma histórico, calculamos reales y virtuales
                    for c_id, c_ini_str, c_fin_str in cronos:
                        # Determinar personal activo en este cronograma
                        activos = []
                        for emp in ctx.empleados:
                            if emp.fecha_inicio_historial and emp.fecha_inicio_historial <= c_fin_str:
                                activos.append(emp)
                        
                        if not activos:
                            activos = ctx.empleados
                            
                        tot_turnos = 0
                        turnos_reales = {emp.nombre: 0 for emp in activos}
                        for emp in activos:
                            cnt = guardias_by_emp_crono.get((c_id, emp.nombre), 0)
                            turnos_reales[emp.nombre] = cnt
                            tot_turnos += cnt
                            
                        num_activos = len(activos)
                        avg_turnos = tot_turnos / num_activos if num_activos > 0 else 0
                        
                        # Asignar a cada empleado (real si estuvo activo, promedio virtual si estuvo inactivo)
                        for emp in ctx.empleados:
                            if emp in activos:
                                turnos_historicos[emp.nombre] += turnos_reales[emp.nombre]
                            else:
                                turnos_historicos[emp.nombre] += avg_turnos
    else:
        # Si la nivelación no está activa, usar los acumulados precalculados de la DB
        for emp in ctx.empleados:
            turnos_historicos[emp.nombre] = float(emp.noches_previas) if emp.noches_previas else 0.0

    # 3. Calcular ratios históricos y el floor ratio
    ratios_historicos = {}
    empleados_activos_regla = []
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_TURNO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params):
            empleados_activos_regla.append(emp.nombre)
            d_hist = dias_disponibles_historicos[emp.nombre]
            if d_hist > 0:
                ratios_historicos[emp.nombre] = turnos_historicos[emp.nombre] / d_hist
            else:
                ratios_historicos[emp.nombre] = 0.0

    ratios_para_floor = [ratios_historicos[nom] for nom in empleados_activos_regla if dias_disponibles_historicos[nom] > 0]
    floor_ratio = min(ratios_para_floor) if ratios_para_floor else 0.0

    # 4. Modelar en OR-Tools CP-SAT aplicando penalización progresiva individual
    peso_global = regla_serv.get('peso', 500) if isinstance(regla_serv, dict) else 500

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'PESO_BRECHA_TURNO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        
        if not _re.regla_suspendida(params):
            # Obtener el peso específico del empleado, con fallback al peso global
            peso_emp = params.get('peso', peso_global) if isinstance(params, dict) else peso_global
            
            # Calcular disponibilidad en el bloque actual
            dias_disponibles_actual = float(ctx.dias - len(emp.dias_licencia))
            d_total = dias_disponibles_historicos[emp.nombre] + dias_disponibles_actual
            
            if d_total <= 0:
                continue

            turnos_mes = []
            for d in range(ctx.dias):
                # Determinar si el día es de fin de semana/feriado o de semana para traer turnos correspondientes
                dia_semana = (d + ctx.offset_dia) % 7
                es_finde_o_feriado = (dia_semana >= 5) or (d in ctx.feriados)
                tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
                
                lista_turnos = ctx.demanda_turnos.get(tipo_dia, {}).keys()
                for t in lista_turnos:
                    if es_turno_objetivo(t, turno_objetivo) and (emp.nombre, d, t) in ctx.turnos:
                        turnos_mes.append(ctx.turnos[(emp.nombre, d, t)])
            
            # Penalización progresiva para los turnos asignados este mes
            if turnos_mes:
                N_turnos = len(turnos_mes)
                at_least_turnos = [modelo.NewBoolVar(f'at_least_brecha_{emp.nombre}_{j}') for j in range(1, N_turnos + 1)]
                modelo.Add(sum(turnos_mes) == sum(at_least_turnos))
                
                for j in range(N_turnos - 1):
                    modelo.Add(at_least_turnos[j] >= at_least_turnos[j + 1])
                    
                t_hist = turnos_historicos[emp.nombre]
                for j, var in enumerate(at_least_turnos):
                    # Ratio resultante si llega al turno j (1-indexed, por lo que usamos j + 1)
                    ratio_j = (t_hist + (j + 1)) / d_total
                    ratio_rel_j = max(0.0, ratio_j - floor_ratio)
                    coeficiente = int(round(ratio_rel_j * peso_emp))
                    
                    if coeficiente > 0:
                        ctx.penalizaciones_soft.append(var * coeficiente)
