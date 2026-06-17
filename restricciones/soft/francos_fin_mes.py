"""
restricciones/soft/francos_fin_mes.py — SOFT
Asegura que en la última semana del mes se asignen los francos correspondientes
para evitar sobrecargar al profesional al inicio del mes siguiente.
Regla: FRANCOS_FIN_MES
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import get_semanas_calendario, is_finde
import rule_engine as _re

def apply(modelo, ctx) -> None:
    # 1. Obtener la última semana calendario
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    semanas = get_semanas_calendario(ctx.dias, fecha_inicio_dt)
    
    if not semanas:
        return
        
    # Ordenar y tomar la última semana del bloque
    semanas_ordenadas = sorted(semanas.keys())
    ultima_sem_key = semanas_ordenadas[-1]
    days = semanas[ultima_sem_key]
    
    # 2. Contar cuántos días de la última semana están dentro de nuestro bloque
    num_dias = len(days)
    
    # 3. Aplicar a cada empleado
    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'FRANCOS_FIN_MES', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        # Si no está configurada, usar valores por defecto
        if params is ...:
            params = {
                "por_dias": {"5": 2, "4": 1},
                "peso": 5000
            }

        peso = params.get('peso', 5000)
        por_dias = params.get('por_dias', {})
        
        # Obtener el target según los días de la última semana
        target_default = por_dias.get(str(num_dias)) or por_dias.get(num_dias)
        if target_default is None:
            continue
            
        try:
            target_default = int(target_default)
        except (ValueError, TypeError):
            continue

        if target_default <= 0:
            continue

        # Filtrar días que no sean licencias
        dias_activos = []
        cantidad_licencias = 0
        for d_idx, _ in days:
            if d_idx in emp.dias_licencia:
                cantidad_licencias += 1
            else:
                dias_activos.append(d_idx)
                
        # Ajustar target de francos según licencias
        target = max(0, target_default - cantidad_licencias)
        if target <= 0 or not dias_activos:
            continue

        francos_present = []
        for d_idx in dias_activos:
            td = "Finde_Feriado" if is_finde(d_idx, ctx.offset_dia, ctx.feriados) else "Semana"
            turnos_dia = [ctx.turnos[(emp.nombre, d_idx, t)]
                          for t in ctx.demanda_turnos.get(td, {}).keys()
                          if (emp.nombre, d_idx, t) in ctx.turnos]
            
            if turnos_dia:
                is_work = sum(turnos_dia)
                is_franco = modelo.NewBoolVar(f"ffm_franco_{emp.nombre}_d{d_idx}")
                modelo.Add(is_franco == 1 - is_work)
                francos_present.append(is_franco)

        if francos_present:
            # v_viol >= target - sum(francos_present)
            # es decir: sum(francos_present) + v_viol >= target
            v_viol = modelo.NewIntVar(0, target, f"ffm_viol_{emp.nombre}")
            modelo.Add(sum(francos_present) + v_viol >= target)
            ctx.penalizaciones_soft.append(v_viol * peso)
