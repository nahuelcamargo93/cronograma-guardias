import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from database.connection import get_connection
from restricciones.hard._utils import get_semanas_calendario

def analizar():
    with get_connection() as conn:
        # 1. Obtener datos del cronograma 360
        crono = conn.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = 360").fetchone()
        if not crono:
            print("No se encontró el cronograma con ID 360.")
            return
        
        fecha_inicio_str, fecha_fin_str = crono
        fecha_inicio_dt = datetime.date.fromisoformat(fecha_inicio_str)
        fecha_fin_dt = datetime.date.fromisoformat(fecha_fin_str)
        total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
        
        print(f"Cronograma 360: {fecha_inicio_str} al {fecha_fin_str} ({total_dias} días)")

        # 2. Obtener las guardias del cronograma
        guardias_rows = conn.execute("""
            SELECT nombre, fecha, turno, horas 
            FROM guardias 
            WHERE cronograma_id = 360
        """).fetchall()
        
        # 3. Obtener los FLRs asignados
        flrs_rows = conn.execute("""
            SELECT nombre, fecha_inicio, fecha_fin 
            FROM flr_asignados 
            WHERE cronograma_id = 360
        """).fetchall()
        
        # 4. Obtener licencias del periodo
        licencias_rows = conn.execute("""
            SELECT nombre, fecha_inicio, fecha_fin 
            FROM licencias
        """).fetchall()

    # Procesar guardias (guardamos qué días trabaja cada empleado)
    trabajo_emp = {}
    empleados = set()
    
    for nombre, fecha_str, turno, horas in guardias_rows:
        empleados.add(nombre)
        f_dt = datetime.date.fromisoformat(fecha_str)
        d_idx = (f_dt - fecha_inicio_dt).days
        # Consideramos como trabajo si el turno no es libre/franco
        if turno not in ('L', 'FRANCO', 'Franco', 'Libre', 'LI', 'LC'):
            trabajo_emp.setdefault(nombre, [False] * total_dias)
            if 0 <= d_idx < total_dias:
                trabajo_emp[nombre][d_idx] = True

    # Inicializar para los empleados que no tengan guardias
    for nombre in empleados:
        if nombre not in trabajo_emp:
            trabajo_emp[nombre] = [False] * total_dias

    # Procesar FLRs asignados por empleado
    flr_dias = {}
    for nombre, f_ini_str, f_fin_str in flrs_rows:
        f_ini = datetime.date.fromisoformat(f_ini_str)
        f_fin = datetime.date.fromisoformat(f_fin_str)
        dias_rango = []
        curr = f_ini
        while curr <= f_fin:
            d_idx = (curr - fecha_inicio_dt).days
            if 0 <= d_idx < total_dias:
                dias_rango.append(d_idx)
            curr += datetime.timedelta(days=1)
        flr_dias.setdefault(nombre, set()).update(dias_rango)

    # Procesar Licencias por empleado
    lic_dias = {}
    for nombre, f_ini_str, f_fin_str in licencias_rows:
        if nombre not in empleados:
            continue
        f_ini = datetime.date.fromisoformat(f_ini_str)
        f_fin = datetime.date.fromisoformat(f_fin_str)
        dias_rango = []
        curr = f_ini
        while curr <= f_fin:
            d_idx = (curr - fecha_inicio_dt).days
            if 0 <= d_idx < total_dias:
                dias_rango.append(d_idx)
            curr += datetime.timedelta(days=1)
        lic_dias.setdefault(nombre, set()).update(dias_rango)

    semanas = get_semanas_calendario(total_dias, fecha_inicio_dt)

    print("\n--- 1. ANÁLISIS: MÁS DE 3 FRANCOS POR SEMANA ---")
    infracciones_semana = 0
    for nombre in sorted(empleados):
        for (iso_y, iso_w), days in semanas.items():
            if len(days) < 7:
                continue # Ignorar semanas incompletas/limítrofes igual que en max_francos_semana.py
            
            # Contar francos en esta semana (días no trabajados y no licencias)
            cant_francos = 0
            dias_semana_list = [d_idx for d_idx, _ in days]
            for d_idx in dias_semana_list:
                es_lic = d_idx in lic_dias.get(nombre, set())
                es_trabajo = trabajo_emp[nombre][d_idx]
                if not es_trabajo and not es_lic:
                    cant_francos += 1
            
            if cant_francos > 3:
                infracciones_semana += 1
                fechas_sem = f"{days[0][1]} a {days[-1][1]}"
                print(f"  [ALERTA] {nombre} tiene {cant_francos} francos en la semana {iso_w} ({fechas_sem})")
    
    if infracciones_semana == 0:
        print("  [OK] Nadie tiene más de 3 francos en semanas completas.")

    print("\n--- 2. ANÁLISIS: 4 O MÁS FRANCOS SEGUIDOS (SIN CONTAR FLR Y LICENCIAS) ---")
    infracciones_cont = 0
    for nombre in sorted(empleados):
        # Determinar si cada día es franco real (no trabajo, no FLR, no licencia)
        es_franco = []
        for d in range(total_dias):
            es_lic = d in lic_dias.get(nombre, set())
            es_flr = d in flr_dias.get(nombre, set())
            es_trabajo = trabajo_emp[nombre][d]
            # Si no trabaja, no es FLR, y no es licencia => franco
            es_franco.append(not es_trabajo and not es_flr and not es_lic)
            
        # Analizar secuencias
        racha = 0
        racha_inicio = None
        for d, val in enumerate(es_franco):
            if val:
                if racha == 0:
                    racha_inicio = d
                racha += 1
            else:
                if racha >= 4:
                    infracciones_cont += 1
                    fecha_ini_r = fecha_inicio_dt + datetime.timedelta(days=racha_inicio)
                    fecha_fin_r = fecha_inicio_dt + datetime.timedelta(days=d - 1)
                    print(f"  [ALERTA] {nombre} tiene {racha} francos seguidos del {fecha_ini_r} al {fecha_fin_r}")
                racha = 0
                
        # Verificar al final del mes
        if racha >= 4:
            infracciones_cont += 1
            fecha_ini_r = fecha_inicio_dt + datetime.timedelta(days=racha_inicio)
            fecha_fin_r = fecha_inicio_dt + datetime.timedelta(days=total_dias - 1)
            print(f"  [ALERTA] {nombre} tiene {racha} francos seguidos del {fecha_ini_r} al {fecha_fin_r} (fin de mes)")

    if infracciones_cont == 0:
        print("  [OK] Nadie tiene 4 o más francos seguidos (excluyendo FLR y licencias).")

if __name__ == "__main__":
    analizar()
