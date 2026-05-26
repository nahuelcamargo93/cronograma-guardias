import sqlite3
import pandas as pd
from datetime import date
import sys

def generar_reporte():
    try:
        conn = sqlite3.connect('cronograma_inteligente.db')
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return

    # 1. Rango de fechas del historial
    range_query = "SELECT MIN(fecha), MAX(fecha) FROM guardias"
    res = conn.execute(range_query).fetchone()
    if not res or not res[0]:
        print("No se encontraron guardias grabadas en la base de datos para generar el reporte.")
        return
    
    start_str, end_str = res
    start_date = date.fromisoformat(start_str)
    end_date = date.fromisoformat(end_str)
    total_days = (end_date - start_date).days + 1
    total_weeks = total_days / 7.0

    # 2. Cargar Personal
    personal = pd.read_sql_query("SELECT nombre, rol FROM personal", conn)
    
    # 3. Cargar Horas Trabajadas
    horas_trabajadas = pd.read_sql_query("""
        SELECT nombre, SUM(horas) as horas_trabajadas
        FROM guardias
        GROUP BY nombre
    """, conn)
    
    # 4. Cargar Fines de Semana Trabajados (FS)
    # Se cuenta cada semana ISO donde la persona tuvo al menos una guardia en fin de semana
    fs_trabajados = pd.read_sql_query("""
        SELECT nombre, COUNT(DISTINCT strftime('%Y-%W', fecha)) as fs
        FROM guardias
        WHERE es_finde = 1
        GROUP BY nombre
    """, conn)

    # 4b. Cargar Noches Trabajadas
    noches_trabajadas = pd.read_sql_query("""
        SELECT nombre, COUNT(*) as noches
        FROM guardias
        WHERE turno LIKE 'Noche%'
        GROUP BY nombre
    """, conn)
    
    # 5. Cargar Fines de Semana Largos (FSL3, FSL4)
    bloques = pd.read_sql_query("SELECT id, fecha_inicio, fecha_fin, tipo FROM bloques_finde_largo", conn)
    fsl3_counts = {n: 0 for n in personal['nombre']}
    fsl4_counts = {n: 0 for n in personal['nombre']}
    
    for _, b in bloques.iterrows():
        trab_bloque = pd.read_sql_query(f"SELECT DISTINCT nombre FROM guardias WHERE fecha BETWEEN '{b['fecha_inicio']}' AND '{b['fecha_fin']}' AND es_finde = 1", conn)['nombre'].tolist()
        for n in trab_bloque:
            if n in fsl3_counts:
                if b['tipo'] == 3: fsl3_counts[n] += 1
                elif b['tipo'] >= 4: fsl4_counts[n] += 1

    # 6. Calcular Horas Disponibles (Capacidad teórica)
    try:
        import json
        regla_hs = conn.execute("SELECT parametros_json FROM servicios_reglas WHERE codigo_regla = 'MAX_HORAS_SEMANA'").fetchone()
        max_hs_semana = json.loads(regla_hs[0])['limite'] if regla_hs else 36
    except:
        max_hs_semana = 36

    licencias = pd.read_sql_query("SELECT nombre, fecha_inicio, fecha_fin FROM licencias", conn)
    
    # 7. Ensamblar Reporte
    reporte = personal.merge(horas_trabajadas, on='nombre', how='left').fillna(0)
    reporte = reporte.merge(fs_trabajados, on='nombre', how='left').fillna(0)
    reporte = reporte.merge(noches_trabajadas, on='nombre', how='left').fillna(0)
    reporte['fsl3'] = reporte['nombre'].map(fsl3_counts)
    reporte['fsl4'] = reporte['nombre'].map(fsl4_counts)
    
    hs_disp_list = []
    for _, row in reporte.iterrows():
        nombre = row['nombre']
        lic_pers = licencias[licencias['nombre'] == nombre]
        dias_lic = 0
        for _, l in lic_pers.iterrows():
            l_ini = max(start_date, date.fromisoformat(l['fecha_inicio']))
            l_fin = min(end_date, date.fromisoformat(l['fecha_fin']))
            if l_ini <= l_fin:
                dias_lic += (l_fin - l_ini).days + 1
        dias_efectivos = total_days - dias_lic
        hs_disp = (dias_efectivos / 7.0) * max_hs_semana
        hs_disp_list.append(round(hs_disp, 1))
        
    reporte['horas_disponibles'] = hs_disp_list
    reporte['ocupacion'] = reporte.apply(lambda x: round((x['horas_trabajadas'] / x['horas_disponibles'] * 100), 1) if x['horas_disponibles'] > 0 else 0, axis=1)
    reporte = reporte.sort_values(by='ocupacion', ascending=False)
    
    # 8. Guardar en Excel
    output_file = 'Reporte_Carga_Historica.xlsx'
    try:
        reporte.to_excel(output_file, index=False, engine='xlsxwriter')
        print(f"\n[OK] Reporte guardado en: {output_file}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo guardar el Excel: {e}")

    # Imprimir en consola
    print("\n" + "="*80)
    print(f"REPORTE ESTÁTICO DE CARGA (Historial en DB)")
    print(f"Período: {start_str} al {end_str} ({total_weeks:.1f} semanas)")
    print("="*80)
    print(reporte[['nombre', 'horas_trabajadas', 'horas_disponibles', 'ocupacion', 'fs', 'noches', 'fsl3', 'fsl4']].to_string(index=False))
    print("="*80 + "\n")
    
    conn.close()

if __name__ == "__main__":
    generar_reporte()
