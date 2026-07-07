import sys, os
sys.path.append(os.getcwd())

from database.data_loader import obtener_empleados
from database.queries import cargar_reglas_servicio, obtener_feriados
import rule_engine as _re
from datetime import date, timedelta

MAPA_DIAS = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
             "Viernes": 4, "Sabado": 5, "Domingo": 6}

servicio_id = 1
fecha_inicio = "2026-08-01"
empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
reglas_servicio = cargar_reglas_servicio(servicio_id)

# Cargar ajustes de reglas personales
from database.queries import cargar_ajustes_reglas_personal
ajustes = cargar_ajustes_reglas_personal(servicio_id, fecha_inicio)

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
offset_dia = fecha_inicio_dt.weekday()
feriados = set()

for emp in empleados:
    if emp.nombre != 'Toledo, Andrea':
        continue
    
    print(f"=== {emp.nombre} (rol={emp.rol}) ===")
    print(f"  dias_licencia: {emp.dias_licencia}")
    
    for d in range(31):
        dia_semana = (d + offset_dia) % 7
        if dia_semana >= 5:
            continue  # Solo analizar días hábiles
            
        fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
        dia_nombre = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][dia_semana]
        
        params = _re.resolver_parametros_regla(
            'ASIGNACION_FIJA', emp.nombre, fecha_d,
            reglas_servicio, emp.reglas, ajustes
        )
        
        params_franco = _re.resolver_parametros_regla(
            'FRANCO_FORZADO', emp.nombre, fecha_d,
            reglas_servicio, emp.reglas, ajustes
        )
        tiene_franco = _re.regla_existe(params_franco) and not _re.regla_suspendida(params_franco)
        es_licencia = d in emp.dias_licencia
        
        # Simular la lógica del constraint
        forzados = []
        if _re.regla_existe(params) and isinstance(params, list):
            for asig in params:
                fecha_asig = asig.get('Fecha')
                dia_asig = asig.get('Dia')
                turno_fijo = asig.get('Turno', '').replace(" ", "_")
                
                es_por_fecha = bool(fecha_asig and fecha_asig == fecha_d)
                es_por_dia = bool(dia_asig and MAPA_DIAS.get(dia_asig) == dia_semana and d not in feriados)
                
                forzar = False
                if es_por_fecha:
                    forzar = True
                elif es_por_dia:
                    if not tiene_franco:
                        forzar = True
                
                if forzar:
                    forzados.append(turno_fijo)
        
        # Solo reportar días sin forzar
        if not forzados:
            print(f"  d={d:2d} {fecha_d} ({dia_nombre}): NO FORZADO | licencia={es_licencia}, franco={tiene_franco}, regla_existe={_re.regla_existe(params)}")
        else:
            # Verificar que sí se debería forzar
            pass  # print(f"  d={d:2d} {fecha_d} ({dia_nombre}): FORZAR {forzados}")
