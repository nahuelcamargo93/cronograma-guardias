"""
restricciones/soft/equidad_fsl.py — SOFT
Nivelación histórica unificada para fines de semana largos (FSL3 y FSL4) en una única regla paramétrica.
Regla: PESO_EQUIDAD_FSL
"""
from datetime import date, timedelta
import rule_engine as _re
from database.connection import get_connection

def _bloques_largos(ctx):
    """Retorna los bloques de días consecutivos de descanso (fin de semana largo) del mes actual."""
    es_descanso = [
        ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados)
        for d in range(ctx.dias)
    ]
    bloques = []
    actual = []
    for d in range(ctx.dias):
        if es_descanso[d]:
            actual.append(d)
        else:
            if len(actual) >= 3:
                bloques.append(actual)
            actual = []
    if len(actual) >= 3:
        bloques.append(actual)
    return bloques

def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    
    # 1. Obtener la regla y ver si tiene nivelación histórica
    codigo_activo = 'PESO_EQUIDAD_FSL' if 'PESO_EQUIDAD_FSL' in ctx.reglas_servicio else 'EQUIDAD_FSL'
    regla_serv = ctx.reglas_servicio.get(codigo_activo)
    if not regla_serv:
        # Verificar si al menos un empleado tiene la regla activa de manera individual
        tiene_regla = False
        for emp in ctx.empleados:
            params = _re.resolver_parametros_regla(
                codigo_activo, emp.nombre, ctx.fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_suspendida(params):
                tiene_regla = True
                break
        if not tiene_regla:
            return
        regla_serv = {}
        
    nivelacion_config = regla_serv.get('nivelacion_historica') if isinstance(regla_serv, dict) else None
    
    fl3_historicos = {emp.nombre: 0.0 for emp in ctx.empleados}
    fl4_historicos = {emp.nombre: 0.0 for emp in ctx.empleados}
    
    # 2. Si la nivelación está activa, calcular históricos reales y virtuales
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
                    
                    with get_connection() as conn:
                        # Bloques de esos cronogramas
                        bloques_hist = conn.execute(f"""
                            SELECT cronograma_id, fecha_inicio, fecha_fin, tipo
                            FROM bloques_finde_largo
                            WHERE cronograma_id IN ({placeholders})
                        """, crono_ids).fetchall()
                        
                        # Guardias es_finde de esos cronogramas
                        guardias_hist = conn.execute(f"""
                            SELECT g.nombre, g.fecha, g.cronograma_id
                            FROM guardias g
                            JOIN personal p ON g.nombre = p.nombre
                            WHERE g.cronograma_id IN ({placeholders})
                              AND g.es_finde = 1
                              AND p.servicio_id = ?
                        """, crono_ids + [ctx.servicio_id]).fetchall()
                        
                    guardias_by_emp_crono = {}
                    for nom, fecha_str, c_id in guardias_hist:
                        guardias_by_emp_crono.setdefault((c_id, nom), set()).add(fecha_str)
                    
                    # Para cada cronograma histórico, calculamos reales y virtuales
                    for c_id, c_ini_str, c_fin_str in cronos:
                        # Determinar personal activo en este cronograma
                        activos = []
                        for emp in ctx.empleados:
                            if emp.fecha_inicio_historial and emp.fecha_inicio_historial <= c_fin_str:
                                activos.append(emp)
                        
                        # Si nadie está marcado como activo (por falta de historial cargado),
                        # consideramos a todos activos para evitar división por cero.
                        if not activos:
                            activos = ctx.empleados
                            
                        # Bloques de este cronograma específico
                        c_bloques = [b for b in bloques_hist if b[0] == c_id]
                        
                        # Contar FSL reales para los activos en este cronograma
                        trabajados_fl3 = {emp.nombre: 0 for emp in activos}
                        trabajados_fl4 = {emp.nombre: 0 for emp in activos}
                        
                        tot_fl3 = 0
                        tot_fl4 = 0
                        
                        for _, fi_str, ff_str, tipo in c_bloques:
                            fi_dt = date.fromisoformat(fi_str)
                            ff_dt = date.fromisoformat(ff_str)
                            bloque_fechas = [(fi_dt + timedelta(days=d)).isoformat() for d in range((ff_dt - fi_dt).days + 1)]
                            
                            for emp in activos:
                                emp_g_dates = guardias_by_emp_crono.get((c_id, emp.nombre), set())
                                if any(d_str in emp_g_dates for d_str in bloque_fechas):
                                    if tipo == 3:
                                        trabajados_fl3[emp.nombre] += 1
                                        tot_fl3 += 1
                                    elif tipo >= 4:
                                        trabajados_fl4[emp.nombre] += 1
                                        tot_fl4 += 1
                                        
                        # Promedios de este cronograma
                        num_activos = len(activos)
                        avg_fl3 = tot_fl3 / num_activos
                        avg_fl4 = tot_fl4 / num_activos
                        
                        # Asignar a cada empleado (real si estuvo activo, promedio virtual si estuvo inactivo)
                        for emp in ctx.empleados:
                            if emp in activos:
                                fl3_historicos[emp.nombre] += trabajados_fl3[emp.nombre]
                                fl4_historicos[emp.nombre] += trabajados_fl4[emp.nombre]
                            else:
                                fl3_historicos[emp.nombre] += avg_fl3
                                fl4_historicos[emp.nombre] += avg_fl4
                                
    else:
        # Si la nivelación no está activa, usar los acumulados precalculados de la DB
        for emp in ctx.empleados:
            fl3_historicos[emp.nombre] = float(emp.findes_largos_3_previos)
            fl4_historicos[emp.nombre] = float(emp.findes_largos_4_previos)

    # 3. Modelar en OR-Tools CP-SAT
    bloques = _bloques_largos(ctx)
    max_fl3 = modelo.NewIntVar(0, 100, 'max_fl3')
    min_fl3 = modelo.NewIntVar(0, 100, 'min_fl3')
    max_fl4 = modelo.NewIntVar(0, 100, 'max_fl4')
    min_fl4 = modelo.NewIntVar(0, 100, 'min_fl4')

    totales_fl3 = []
    totales_fl4 = []

    for emp in ctx.empleados:
        fl3_mes, fl4_mes = [], []
        for bloque in bloques:
            t_f_names = ctx.demanda_turnos.get('Finde_Feriado', {}).keys()
            vars_b = [
                ctx.turnos[(emp.nombre, d, t)]
                for d in bloque for t in t_f_names
                if (emp.nombre, d, t) in ctx.turnos
            ]
            if vars_b:
                trabaja = modelo.NewBoolVar(f'trabaja_fl_{emp.nombre}_b{bloque[0]}')
                modelo.AddMaxEquality(trabaja, vars_b)
                if len(bloque) == 3:
                    fl3_mes.append(trabaja)
                elif len(bloque) >= 4:
                    fl4_mes.append(trabaja)

        params = _re.resolver_parametros_regla(
            codigo_activo, emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        
        if not _re.regla_suspendida(params):
            h3_int = int(round(fl3_historicos.get(emp.nombre, 0.0)))
            h4_int = int(round(fl4_historicos.get(emp.nombre, 0.0)))
            
            total_fl3_var = modelo.NewIntVar(0, 100, f'total_fl3_{emp.nombre}')
            modelo.Add(total_fl3_var == h3_int + (sum(fl3_mes) if fl3_mes else 0))
            totales_fl3.append(total_fl3_var)

            total_fl4_var = modelo.NewIntVar(0, 100, f'total_fl4_{emp.nombre}')
            modelo.Add(total_fl4_var == h4_int + (sum(fl4_mes) if fl4_mes else 0))
            totales_fl4.append(total_fl4_var)

    # 4. Aplicar penalizaciones
    peso_fl3 = regla_serv.get('peso_fl3', regla_serv.get('peso', 500))
    peso_fl4 = regla_serv.get('peso_fl4', regla_serv.get('peso', 500))

    if totales_fl3:
        modelo.AddMaxEquality(max_fl3, totales_fl3)
        modelo.AddMinEquality(min_fl3, totales_fl3)
        ctx.penalizaciones_soft.append((max_fl3 - min_fl3) * peso_fl3)

    if totales_fl4:
        modelo.AddMaxEquality(max_fl4, totales_fl4)
        modelo.AddMinEquality(min_fl4, totales_fl4)
        ctx.penalizaciones_soft.append((max_fl4 - min_fl4) * peso_fl4)
