import sqlite3
import json
from datetime import date, timedelta

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Obtener el último cronograma generado
    crono_row = cursor.execute("SELECT id, fecha_inicio, fecha_fin FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    if not crono_row:
        print("No se encontraron cronogramas en la base de datos.")
        return
        
    crono_id, fecha_inicio_str, fecha_fin_str = crono_row
    print(f"Analizando Cronograma ID: {crono_id} ({fecha_inicio_str} -> {fecha_fin_str})")
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio_str)
    fecha_fin_dt = date.fromisoformat(fecha_fin_str)
    dias_totales = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # 2. Cargar regla MANEJO_FINDES del servicio 2
    regla_row = cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=2 AND codigo_regla='MANEJO_FINDES'").fetchone()
    if not regla_row:
        print("No se encontró la regla MANEJO_FINDES para el servicio 2.")
        return
    params = json.loads(regla_row[0])
    por_disponibilidad = params.get('por_disponibilidad', {})
    
    # 3. Mapear fines de semana en el mes
    # d0, d1, d7, d8, d14, d15, d21, d22, d28, d29
    findes = {} # lunes_semana -> list of (fecha_dt, dia_semana)
    for d in range(dias_totales):
        fd = fecha_inicio_dt + timedelta(days=d)
        wd = fd.weekday()
        if wd in (5, 6):
            lunes = (fd - timedelta(days=wd)).isoformat()
            findes.setdefault(lunes, []).append(fd)
            
    # 4. Cargar personal del servicio 2
    empleados = cursor.execute("SELECT nombre FROM personal WHERE servicio_id=2 AND activo=1").fetchall()
    empleados = [e[0] for e in empleados]
    
    # 5. Cargar licencias del mes
    licencias_by_emp = {}
    lic_rows = cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM licencias WHERE nombre IN (SELECT nombre FROM personal WHERE servicio_id=2)").fetchall()
    for nom, fi, ff in lic_rows:
        licencias_by_emp.setdefault(nom, []).append((date.fromisoformat(fi), date.fromisoformat(ff)))
        
    # 6. Cargar guardias asignadas en este cronograma
    guardias_rows = cursor.execute("SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id=?", (crono_id,)).fetchall()
    guardias_by_emp = {}
    for nom, fecha, turno in guardias_rows:
        guardias_by_emp.setdefault(nom, {}).setdefault(fecha, []).append(turno)
        
    # 7. Cargar FLRs asignados
    flrs_rows = cursor.execute("SELECT nombre, fecha_inicio FROM flr_asignados WHERE cronograma_id=?", (crono_id,)).fetchall()
    flrs_by_emp = {}
    for nom, fi in flrs_rows:
        flrs_by_emp.setdefault(nom, []).append(fi)
        
    print("\n--- INFORME DE DESVIACIONES EN MANEJO_FINDES ---")
    violaciones_detectadas = 0
    
    for emp_nom in sorted(empleados):
        # Calcular disponibilidad del empleado
        emp_lics = licencias_by_emp.get(emp_nom, [])
        
        def disponible(dia_dt):
            for l_ini, l_fin in emp_lics:
                if l_ini <= dia_dt <= l_fin:
                    return False
            return True
            
        k_disp = sum(
            1 for lunes, dias_f in findes.items()
            if any(disponible(d) for d in dias_f)
        )
        
        # Targets esperados
        conf_disp = por_disponibilidad.get(str(k_disp), {})
        if not conf_disp:
            # Si no hay targets configurados para esa disponibilidad, omitir
            continue
            
        target_flr = conf_disp.get('flr', 0)
        target_c = conf_disp.get('completos', 0)
        target_m = conf_disp.get('medios', 0)
        
        # Evaluar asignaciones reales
        reales_c = 0
        reales_m = 0
        reales_flr = len(flrs_by_emp.get(emp_nom, []))
        
        emp_guardias = guardias_by_emp.get(emp_nom, {})
        
        for lunes, dias_f in findes.items():
            trabajo_sat = False
            trabajo_sun = False
            
            d_sat = next((d for d in dias_f if d.weekday() == 5), None)
            d_sun = next((d for d in dias_f if d.weekday() == 6), None)
            
            if d_sat and d_sat.isoformat() in emp_guardias:
                trabajo_sat = True
            if d_sun and d_sun.isoformat() in emp_guardias:
                trabajo_sun = True
                
            if trabajo_sat and trabajo_sun:
                reales_c += 1
            elif trabajo_sat or trabajo_sun:
                reales_m += 1
                
        # Comparar con los targets
        detalles = []
        if reales_flr < target_flr:
            detalles.append(f"FLR faltante (target={target_flr}, real={reales_flr})")
        elif reales_flr > target_flr:
            detalles.append(f"FLR excedido (target={target_flr}, real={reales_flr})")
            
        if reales_c < target_c:
            detalles.append(f"Finde Completo faltante (target={target_c}, real={reales_c})")
        elif reales_c > target_c:
            detalles.append(f"Finde Completo excedido (target={target_c}, real={reales_c})")
            
        if reales_m < target_m:
            detalles.append(f"Finde Medio faltante (target={target_m}, real={reales_m})")
        elif reales_m > target_m:
            detalles.append(f"Finde Medio excedido (target={target_m}, real={reales_m})")
            
        if detalles:
            violaciones_detectadas += 1
            print(f"Profesional: {emp_nom} (Disp={k_disp} findes)")
            for d in detalles:
                print(f"  -> {d}")
            print(f"  Asignaciones: Completos={reales_c}, Medios={reales_m}, FLR={reales_flr}")
            
    # Conteo general de FLRs para responder la pregunta del usuario
    total_requieren_flr = 0
    total_asignados_flr = 0
    print("\n--- RESUMEN DE ASIGNACIÓN DE FLR ---")
    for emp_nom in sorted(empleados):
        emp_lics = licencias_by_emp.get(emp_nom, [])
        def disponible(dia_dt):
            for l_ini, l_fin in emp_lics:
                if l_ini <= dia_dt <= l_fin:
                    return False
            return True
        k_disp = sum(1 for lunes, dias_f in findes.items() if any(disponible(d) for d in dias_f))
        conf_disp = por_disponibilidad.get(str(k_disp), {})
        target_flr = conf_disp.get('flr', 0)
        reales_flr = len(flrs_by_emp.get(emp_nom, []))
        
        if target_flr > 0:
            total_requieren_flr += 1
            if reales_flr > 0:
                total_asignados_flr += 1
            else:
                print(f"⚠️ Profesional {emp_nom} REQUIERE FLR pero NO tiene ninguno asignado.")
        elif reales_flr > 0:
            print(f"⚠️ Profesional {emp_nom} NO REQUIERE FLR pero tiene {reales_flr} asignado(s).")
            
    print(f"Total profesionales que requieren FLR (Disp >= 4): {total_requieren_flr}")
    print(f"Total profesionales con FLR asignado: {total_asignados_flr}")

    if violaciones_detectadas == 0:
        print("\n¡No se detectaron violaciones! La regla se cumplió perfectamente para todos.")
    else:
        print(f"\nTotal profesionales con desvíos en targets: {violaciones_detectadas}")

if __name__ == '__main__':
    main()
