from typing import List, Dict
from models import Empleado, Turno
from database import queries as q
from datetime import date, timedelta

def get_dias_y_tipos_licencia(nombre: str, fecha_inicio_dt: date, dias_del_bloque: int) -> tuple[set, dict]:
    bloqueados = set()
    tipos = {}
    for tipo_nombre, licencias_dict in [('LAR', q.LAR), ('LPP', q.LPP), ('LM', q.LM), ('CM', q.CM), ('LI', q.LI)]:
        for (lic_ini_str, lic_fin_str) in licencias_dict.get(nombre, []):
            lic_ini = date.fromisoformat(lic_ini_str)
            lic_fin = date.fromisoformat(lic_fin_str)
            for d in range(dias_del_bloque):
                if lic_ini <= fecha_inicio_dt + timedelta(days=d) <= lic_fin:
                    bloqueados.add(d)
                    tipos[d] = tipo_nombre
    return bloqueados, tipos

def obtener_empleados(servicio_id: int, fecha_inicio: str, dias_del_bloque: int) -> List[Empleado]:
    import pandas as pd
    
    # 1. Obtener datos crudos
    df = pd.DataFrame(q.obtener_personal_db(servicio_id))
    if df.empty:
        return []
        
    df = q.cargar_datos_personales_bd(df)
    historial = q.cargar_historial(df, fecha_inicio)
    reglas_db = q.cargar_reglas_personal(servicio_id)
    reglas_rol_db = q.cargar_reglas_rol(servicio_id)
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    
    empleados: List[Empleado] = []
    
    for _, row in df.iterrows():
        nombre = row['Nombre']
        rol = row.get('Rol', '')
        categoria = row.get('Categoria')
        hist = historial.get(nombre, {})
        
        # Combinar reglas: prioridad baja (rol) < prioridad alta (personal)
        reglas = {}
        if rol and rol in reglas_rol_db:
            reglas.update(reglas_rol_db[rol])
        reglas.update(reglas_db.get(nombre, {}))
        
        # Calcular Horas_Fijas_Semanales
        asigs = reglas.get('ASIGNACION_FIJA', [])
        horas_fijas = sum(a.get('Horas', 0) for a in asigs if isinstance(a, dict))
        
        # Fallback de puestos habilitados en memoria si no están configurados en la DB
        puestos_hab = set(row.get('Puestos_Habilitados', []))
        puestos_prim = set(row.get('Puestos_Primarios', []))
        if not puestos_hab:
            if rol in ('Rotativo', 'Nocturno'):
                puestos_hab = {'UTI', 'UCO', 'General'}
                puestos_prim = {'UTI', 'UCO', 'General'}
            elif rol == 'UTI':
                puestos_hab = {'UTI'}
                puestos_prim = {'UTI'}
            elif rol == 'UCO':
                puestos_hab = {'UCO'}
                puestos_prim = {'UCO'}
            elif rol == 'General':
                puestos_hab = {'General'}
                puestos_prim = {'General'}
            elif rol == 'Especial':
                puestos_hab = {'Especial'}
                puestos_prim = {'Especial'}
            else:
                # Si no coincide el rol, intentar usar la categoría como fallback de compatibilidad
                if categoria == 'UTI':
                    puestos_hab = {'UTI'}
                    puestos_prim = {'UTI'}
                elif categoria == 'UCO':
                    puestos_hab = {'UCO'}
                    puestos_prim = {'UCO'}
                elif categoria == 'Ambos':
                    puestos_hab = {'UTI', 'UCO'}
                    puestos_prim = {'UTI', 'UCO'}
                elif categoria == 'GENERAL':
                    puestos_hab = {'UTI', 'UCO', 'General'}
                    puestos_prim = {'UTI', 'UCO', 'General'}
        
        dias_lic, tipos_lic = get_dias_y_tipos_licencia(nombre, fecha_inicio_dt, dias_del_bloque)
        emp = Empleado(
            nombre=nombre,
            rol=rol,
            categoria=categoria,
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
            dias_licencia=dias_lic,
            tipos_licencia=tipos_lic,
            puestos_habilitados=puestos_hab,
            puestos_primarios=puestos_prim,
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
