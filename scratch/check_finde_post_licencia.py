import sqlite3
from datetime import date, timedelta
import sys

# Agregar path para poder importar módulos del proyecto
sys.path.append(".")
import rule_engine as _re
from database.data_loader import obtener_empleados
import database.queries as db_queries

DB_PATH = "cronograma_inteligente"

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    # IMPORTANTE: Inicializar licencias en queries.py
    db_queries.init_licencias(servicio_id)
    
    reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas_personal = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas_personal['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
    
    print("--- EVALUACIÓN DETALLADA DE LA REGLA ---")
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    
    # Fines de semana
    findes = {}
    for d in range(31):
        wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
        if wd in (5, 6):
            fd = fecha_inicio_dt + timedelta(days=d)
            lunes = (fd - timedelta(days=wd)).isoformat()
            findes.setdefault(lunes, {})
            if wd == 5: findes[lunes]['sat'] = d
            elif wd == 6: findes[lunes]['sun'] = d
    findes_ordenados = sorted(findes.items(), key=lambda x: x[0])
    
    for emp in empleados:
        if not emp.dias_licencia:
            continue
            
        params = _re.resolver_parametros_regla(
            'FINDE_POST_LICENCIA', emp.nombre, fecha_inicio,
            reglas_servicio, emp.reglas, ajustes_reglas_personal
        )
        existe = _re.regla_existe(params)
        suspendida = _re.regla_suspendida(params)
        
        print(f"\nEmpleado: {emp.nombre}")
        print(f"  Regla Existe: {existe} | Suspendida: {suspendida} | Params: {params}")
        
        if not existe or suspendida:
            continue
            
        configuracion = params.get('configuracion')
        print(f"  Configuración: {configuracion}")
        
        def esta_disponible(d):
            if d in emp.dias_licencia:
                return False, "LICENCIA"
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                reglas_servicio, emp.reglas, ajustes_reglas_personal
            )
            if _re.regla_existe(p) and not _re.regla_suspendida(p):
                return False, f"FRANCO_FORZADO ({p})"
            return True, "OK"

        dias_vuelta = []
        for d in sorted(emp.dias_licencia):
            d_vuelta = d + 1
            if d_vuelta < 31 and d_vuelta not in emp.dias_licencia:
                dias_vuelta.append(d_vuelta)
                
        for d_vuelta in dias_vuelta:
            vuelta_fecha = (fecha_inicio_dt + timedelta(days=d_vuelta)).isoformat()
            finde_obj = None
            for lunes_iso, dias_f in findes_ordenados:
                d_sat = dias_f.get('sat')
                d_sun = dias_f.get('sun')
                es_pos = False
                if d_sat is not None and d_sat >= d_vuelta: es_pos = True
                if d_sun is not None and d_sun >= d_vuelta: es_pos = True
                if es_pos:
                    finde_obj = (lunes_iso, d_sat, d_sun)
                    break
                    
            if finde_obj:
                lunes_iso, d_sat, d_sun = finde_obj
                sat_fecha = (fecha_inicio_dt + timedelta(days=d_sat)).isoformat() if d_sat is not None else "N/A"
                sun_fecha = (fecha_inicio_dt + timedelta(days=d_sun)).isoformat() if d_sun is not None else "N/A"
                
                disp_sat, motivo_sat = esta_disponible(d_sat) if d_sat is not None else (False, "N/A")
                disp_sun, motivo_sun = esta_disponible(d_sun) if d_sun is not None else (False, "N/A")
                
                print(f"    Vuelta: día {d_vuelta} ({vuelta_fecha})")
                print(f"    Finde: Sábado {sat_fecha} (Disp: {disp_sat}, Motivo: {motivo_sat}) | Domingo {sun_fecha} (Disp: {disp_sun}, Motivo: {motivo_sun})")
                
    conn.close()

if __name__ == "__main__":
    main()
