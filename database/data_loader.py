from typing import List, Dict
from models import Empleado, Turno
from database import queries as q
from datetime import date, timedelta

def get_dias_licencia(nombre: str, fecha_inicio_dt: date, dias_del_bloque: int) -> set:
    bloqueados = set()
    for licencias in (q.LAR, q.LPP, q.LM, q.CM):
        for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
            lic_ini = date.fromisoformat(lic_ini_str)
            lic_fin = date.fromisoformat(lic_fin_str)
            for d in range(dias_del_bloque):
                if lic_ini <= fecha_inicio_dt + timedelta(days=d) <= lic_fin:
                    bloqueados.add(d)
    return bloqueados

def obtener_empleados(servicio_id: int, fecha_inicio: str, dias_del_bloque: int) -> List[Empleado]:
    import pandas as pd
    
    # 1. Obtener datos crudos
    df = pd.DataFrame(q.obtener_personal_db(servicio_id))
    if df.empty:
        return []
        
    df = q.cargar_datos_personales_bd(df)
    historial = q.cargar_historial(df, fecha_inicio)
    reglas_db = q.cargar_reglas_personal(servicio_id)
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    
    empleados: List[Empleado] = []
    
    for _, row in df.iterrows():
        nombre = row['Nombre']
        hist = historial.get(nombre, {})
        reglas = reglas_db.get(nombre, {})
        
        # Calcular Horas_Fijas_Semanales
        asigs = reglas.get('ASIGNACION_FIJA', [])
        horas_fijas = sum(a.get('Horas', 0) for a in asigs if isinstance(a, dict))
        
        emp = Empleado(
            nombre=nombre,
            rol=row.get('Rol', ''),
            categoria=row.get('Categoria'),
            servicio_id=servicio_id,
            fecha_cumpleanos=row.get('fecha_cumpleanos'),
            es_madre=bool(row.get('es_madre', 0)),
            es_padre=bool(row.get('es_padre', 0)),
            regimen_trabajo=row.get('regimen_trabajo'),
            horas_anuales_previas=hist.get('Horas_Anuales_Previas', 0),
            findes_semanas_previos=hist.get('Findes_Semanas_Previos', 0),
            findes_habiles_previos=hist.get('Findes_Habiles_Previos', 0),
            findes_largos_3_previos=hist.get('Findes_Largos_3_Previos', 0),
            findes_largos_4_previos=hist.get('Findes_Largos_4_Previos', 0),
            feriados_previos=hist.get('Feriados_Previos', 0),
            noches_previas=hist.get('Noches_Previas', 0),
            horas_fijas_semanales=horas_fijas,
            dias_licencia=get_dias_licencia(nombre, fecha_inicio_dt, dias_del_bloque),
            puestos_habilitados=set(row.get('Puestos_Habilitados', [])),
            puestos_primarios=set(row.get('Puestos_Primarios', [])),
            reglas=reglas,
            horas_mensuales_reglamentarias=row.get('horas_mensuales_reglamentarias'),
            fecha_inicio_historial=hist.get('Fecha_Inicio_Historial')
        )
        empleados.append(emp)
        
    return empleados

def obtener_turnos(servicio_id: int) -> Dict[str, Turno]:
    """Carga y retorna un diccionario de objetos Turno."""
    config, turnos_info, _, _ = q.cargar_configuracion_turnos(servicio_id)
    turnos = {}
    for nombre, info in turnos_info.items():
        turnos[nombre] = Turno(
            nombre=nombre,
            horas=info['horas'],
            hora_inicio=info['hora_inicio'],
            puesto_nombre=info.get('puesto_nombre')
        )
    return turnos
