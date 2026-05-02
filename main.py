import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from data import PERSONAL, DEMANDA_TURNOS, calcular_horas_fijas, asignar_horas, TURNOS_SEMANA, TURNOS_FINDE, FECHA_INICIO, FECHA_FIN, FERIADOS
from hard_rules import aplicar_reglas_duras
from soft_rules import aplicar_reglas_blandas
import db as database

def construir_modelo(df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas):
    modelo = cp_model.CpModel()
    
    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    turnos = {}
    
    fecha_inicio_dt_d = date.fromisoformat(FECHA_INICIO)

    def dias_en_licencia(nombre):
        """Devuelve un set de índices de día (0-based) en que la persona está de LAR o LPP."""
        bloqueados = set()
        for licencias in (database.LAR, database.LPP):
            for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
                lic_ini = date.fromisoformat(lic_ini_str)
                lic_fin = date.fromisoformat(lic_fin_str)
                for d in range(dias_del_bloque):
                    if lic_ini <= fecha_inicio_dt_d + timedelta(days=d) <= lic_fin:
                        bloqueados.add(d)
        return bloqueados

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        asignaciones = persona.get('Asignaciones_Fijas', [])
        licencia_dias = dias_en_licencia(nombre)
        for dia in range(dias_del_bloque):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
            lista_turnos = TURNOS_FINDE if es_finde_o_feriado else TURNOS_SEMANA
    
            # 1. Definir variables para este día
            for t in lista_turnos:
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
    
            # 2. Forzar asignaciones fijas
            if dia not in licencia_dias:
                for asig in asignaciones:
                    if mapa_dias.get(asig['Dia']) == dia_semana:
                        turno_config = asig['Turno'].replace(" ", "_")
                        # Buscar todos los turnos que coincidan (ej: "Dia" -> "Dia_UTI", "Dia_UCO")
                        vars_coincidentes = [turnos[(nombre, dia, t)] for t in lista_turnos 
                                             if (t == turno_config or t.startswith(turno_config + "_"))]
                        
                        if vars_coincidentes:
                            modelo.Add(sum(vars_coincidentes) == 1)

    aplicar_reglas_duras(modelo, turnos, df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas)
    aplicar_reglas_blandas(modelo, turnos, df_personal, dias_del_bloque, feriados, offset_dia, num_semanas)
    
    return modelo, turnos

def resolver_modelo(modelo, turnos, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 90
    
    # Validar modelo antes de resolver
    validacion = modelo.Validate()
    if validacion:
        print(f"⚠️ Error de validación en el modelo: {validacion}")
    
    print("Resolviendo el cronograma con todas las reglas y preferencias...")
    status = solver.Solve(modelo)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("¡CRONOGRAMA GENERADO!")
        fecha_inicio_dt = pd.to_datetime(fecha_inicio)
        resultados = []
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for dia in range(dias_del_bloque):
            fecha_actual = fecha_inicio_dt + pd.Timedelta(days=dia)
            dia_semana = dias_nombres[fecha_actual.weekday()]

            es_finde = ((dia + offset_dia) % 7) >= 5 or dia in feriados
            tipos_turnos = TURNOS_FINDE if es_finde else TURNOS_SEMANA

            for t in tipos_turnos:
                for index, persona in df_personal.iterrows():
                    nombre = persona['Nombre']
                    if solver.Value(turnos[(nombre, dia, t)]) == 1:
                        resultados.append({
                            "Fecha": fecha_actual.strftime("%Y-%m-%d"),
                            "Dia_Semana": dia_semana,
                            "Turno": t,
                            "Kinesiologo": nombre
                        })

        df_resultados = pd.DataFrame(resultados)
        return df_resultados
    else:
        print("INVIABLE: El motor no pudo encontrar una solución. Las reglas son muy estrictas.")
        return None

def exportar_excel_data_prep(df_resultados):
    jerarquia = {
        "Lic. Garcia": 1,
        "Lic. Franco": 2,
        "Lic. Moyano": 3,
        "Lic. Toledo": 4
    }

    # Orden deseado de los turnos en el Excel
    orden_turnos_base = [
        "Mañana_UTI", "Mañana_UCO", "Mañana_especial",
        "Tarde_UTI", "Tarde_UCO", "Tarde_especial",
        "Dia_UTI", "Dia_UCO", "Noche"
    ]

    # Reestructurar resultados para tener un kinesiologo por celda
    filas_excel = []
    fechas_unicas = sorted(df_resultados['Fecha'].unique())

    for t_base in orden_turnos_base:
        df_turno = df_resultados[df_resultados['Turno'] == t_base]
        if df_turno.empty:
            continue
            
        # Determinar el máximo de personas en este turno para cualquier día
        max_personas = df_turno.groupby('Fecha').size().max()
        
        for i in range(max_personas):
            fila = {"Turno": t_base if i == 0 else f"{t_base} "} # Espacio para que sea único pero se vea igual
            for fecha in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == fecha].sort_values(
                    by='Kinesiologo', key=lambda x: x.map(lambda n: jerarquia.get(n, 100))
                )['Kinesiologo'].tolist()
                fila[fecha] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # --- AGREGAR FILAS DE LICENCIAS (LAR / LPP) ---
    # Dos filas vacías de separación
    filas_excel.append({"Turno": "  "}) 
    filas_excel.append({"Turno": "   "}) 

    fila_lpp = {"Turno": "LPP"}
    fila_lar = {"Turno": "LAR"}

    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        
        # Buscar quiénes están de LPP este día
        nombres_lpp = []
        for nombre, rangos in database.LPP.items():
            for ini_s, fin_s in rangos:
                if date.fromisoformat(ini_s) <= fecha_dt <= date.fromisoformat(fin_s):
                    nombres_lpp.append(nombre)
                    break
        fila_lpp[fecha] = "\n".join(nombres_lpp)

        # Buscar quiénes están de LAR este día
        nombres_lar = []
        for nombre, rangos in database.LAR.items():
            for ini_s, fin_s in rangos:
                if date.fromisoformat(ini_s) <= fecha_dt <= date.fromisoformat(fin_s):
                    nombres_lar.append(nombre)
                    break
        fila_lar[fecha] = "\n".join(nombres_lar)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)

    df_pivot = pd.DataFrame(filas_excel).set_index("Turno")

    return df_pivot, fechas_unicas

def exportar_excel(df_pivot, df_reporte, fechas_unicas, file_name='Cronograma_Servicio_Kinesiologia.xlsx'):
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        # --- HOJA 1: CRONOGRAMA ---
        df_pivot.to_excel(writer, sheet_name='Cronograma')
        workbook  = writer.book
        worksheet = writer.sheets['Cronograma']

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9})
        uco_fmt = workbook.add_format({'bg_color': '#FFC0CB', 'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9}) # Pink

        colores = {
            "Mañana": '#EBF1DE',
            "Tarde":  '#FEF2CB',
            "Dia":    '#DAEEF3',
            "Noche":  '#E5E0EC'
        }

        worksheet.set_column(0, 0, 18, header_fmt)
        worksheet.set_column(1, len(fechas_unicas), 18, cell_fmt)

        for i, (turno_label, row) in enumerate(df_pivot.iterrows()):
            fila_excel = i + 1
            turno_clean = turno_label.strip().split('_')[0]
            
            if turno_label.strip() in ["LPP", "LAR"]:
                fmt = workbook.add_format({'bg_color': '#F2F2F2', 'italic': True, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 8})
                altura = 35
            elif turno_label.strip() == "":
                fmt = workbook.add_format({'bg_color': '#FFFFFF', 'border': 0})
                altura = 15
            elif "UCO" in turno_label:
                fmt = uco_fmt
                altura = 20
            else:
                color = colores.get(turno_clean, '#FFFFFF')
                fmt = workbook.add_format({'bg_color': color, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 9})
                altura = 20
            
            worksheet.set_row(fila_excel, altura, fmt)

        # --- HOJA 2: REPORTE DE HORAS ---
        df_reporte.to_excel(writer, sheet_name='Reporte de Horas', index=False)
        worksheet_rep = writer.sheets['Reporte de Horas']
        
        rep_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        rep_cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10})
        name_cell_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F2F2F2', 'font_size': 10})
        
        # Formatos alternados para filas
        alt_cell_fmt = workbook.add_format({'bg_color': '#DCE6F1', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10})
        
        # Ajustar anchos de columna
        worksheet_rep.set_column(0, 0, 25, name_cell_fmt) # Kinesiologo
        worksheet_rep.set_column(1, 6, 22, rep_cell_fmt) # Otros
        
        # Aplicar encabezado
        for col_num, value in enumerate(df_reporte.columns.values):
            worksheet_rep.write(0, col_num, value, rep_header_fmt)
        
        # Aplicar formatos a las celdas
        for row_num in range(1, len(df_reporte) + 1):
            fmt = rep_cell_fmt if row_num % 2 != 0 else alt_cell_fmt
            worksheet_rep.set_row(row_num, 20, fmt)
            worksheet_rep.write(row_num, 0, df_reporte.iloc[row_num-1, 0], name_cell_fmt if row_num % 2 != 0 else workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DCE6F1', 'font_size': 10}))

    print(f"¡Excel generado con éxito! Archivo: {file_name}")

def generar_reporte(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, num_semanas):
    df_reporte = df_resultados.copy()
    df_reporte['Horas'] = df_reporte['Turno'].apply(asignar_horas)

    horas_por_persona = df_reporte.groupby('Kinesiologo')['Horas'].sum().reset_index()

    df_reporte['Fecha'] = pd.to_datetime(df_reporte['Fecha'])
    
    # Bloques de findes largos para calculos
    es_descanso = [(((d + offset_dia) % 7) >= 5 or d in feriados) for d in range(dias_del_bloque)]
    bloques = []
    bloque_actual = []
    for d in range(dias_del_bloque):
        if es_descanso[d]: bloque_actual.append(d)
        else:
            if len(bloque_actual) >= 3: bloques.append(bloque_actual)
            bloque_actual = []
    if len(bloque_actual) >= 3: bloques.append(bloque_actual)

    resultados_fl = []
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        turnos_kinesiologo = df_resultados[df_resultados['Kinesiologo'] == nombre]
        fechas_trabajadas = turnos_kinesiologo['Fecha'].tolist()
        
        # Mejor logica para reporte:
        dias_bloqueados = set()
        for licencias in (database.LAR, database.LPP):
            for (ini_s, fin_s) in licencias.get(nombre, []):
                ini = date.fromisoformat(ini_s)
                fin = date.fromisoformat(fin_s)
                for d in range(dias_del_bloque):
                    if ini <= date.fromisoformat(fecha_inicio) + timedelta(days=d) <= fin:
                        dias_bloqueados.add(d)
        
        f_hab_actual = 0
        f_trab_actual = 0
        for sem in range(num_semanas):
            s = sem * 7 + (5 - offset_dia) % 7
            dom = sem * 7 + (6 - offset_dia) % 7
            
            # Habile si no hay licencia ni S ni D
            if s not in dias_bloqueados and dom not in dias_bloqueados:
                f_hab_actual += 1
            
            # Trabajado si hay algun turno en S o D
            f_s = (fecha_inicio_dt + pd.Timedelta(days=s)).strftime("%Y-%m-%d")
            f_dom = (fecha_inicio_dt + pd.Timedelta(days=dom)).strftime("%Y-%m-%d")
            if f_s in fechas_trabajadas or f_dom in fechas_trabajadas:
                f_trab_actual += 1

        fl_3_libres = 0
        fl_4_libres = 0
        for bloque in bloques:
            fechas_bloque = [(fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in bloque]
            trabajo_en_bloque = any(f in fechas_trabajadas for f in fechas_bloque)
            if not trabajo_en_bloque:
                if len(bloque) == 3: fl_3_libres += 1
                elif len(bloque) >= 4: fl_4_libres += 1
                    
        horas_acum = persona.get('Horas_Anuales_Previas', 0) + horas_por_persona[horas_por_persona['Kinesiologo'] == nombre]['Horas'].sum()
        
        f_trab_total = persona.get('Findes_Semanas_Previos', 0) + f_trab_actual
        f_hab_total = persona.get('Findes_Habiles_Previos', 10) + f_hab_actual
        indice_carga = round((f_trab_total / f_hab_total) * 100, 1) if f_hab_total > 0 else 0

        resultados_fl.append({
            'Kinesiologo': nombre,
            'Horas_Anuales_Total': horas_acum,
            'Findes_Actual_Trab': f_trab_actual,
            'Findes_Actual_Hab': f_hab_actual,
            'Findes_Trab_Total': f_trab_total,
            'Findes_Hab_Total': f_hab_total,
            'Indice_Carga_Finde': f"{indice_carga}%",
            'FL3_Total_Acum': persona.get('Findes_Largos_3_Previos', 0) + fl_3_libres,
            'FL4_Total_Acum': persona.get('Findes_Largos_4_Previos', 0) + fl_4_libres
        })
        
    df_fl = pd.DataFrame(resultados_fl)
    reporte_final = pd.merge(horas_por_persona, df_fl, on='Kinesiologo', how='left')

    # Renombrar columnas para el Excel
    reporte_final = reporte_final.rename(columns={
        'Horas': 'Horas del cronograma actual',
        'Horas_Anuales_Total': 'Horas totales anuales',
        'Findes_Actual_Trab': 'Fin de semana actual (Trabajados)',
        'Findes_Actual_Hab': 'Fin de semana actual (Hábiles)',
        'Findes_Trab_Total': 'Acumulado (Trabajados)',
        'Findes_Hab_Total': 'Acumulado (Hábiles)',
        'Indice_Carga_Finde': 'Índice de Carga (%)',
        'FL3_Total_Acum': 'Finde largo 3 dias acumulado',
        'FL4_Total_Acum': 'Finde largo 4 dias acumulado'
    })

    # Ordenar columnas
    columnas_orden = [
        'Kinesiologo',
        'Horas del cronograma actual',
        'Horas totales anuales',
        'Fin de semana actual (Trabajados)',
        'Fin de semana actual (Hábiles)',
        'Acumulado (Trabajados)',
        'Acumulado (Hábiles)',
        'Índice de Carga (%)',
        'Finde largo 3 dias acumulado',
        'Finde largo 4 dias acumulado'
    ]
    reporte_final = reporte_final[columnas_orden]
    reporte_final = reporte_final.sort_values(by='Horas del cronograma actual', ascending=False).reset_index(drop=True)

    print("\nREPORTE DE CONTROL: HORAS Y FINES DE SEMANA")
    print(reporte_final.to_string())
    
    reporte_final.to_csv('Reporte_Horas_Kinesiologia.csv', index=False)
    return reporte_final

def main():
    # --- BASE DE DATOS: inicializar y cargar licencias ---
    database.inicializar_db()
    database.init_licencias()
    print(f"Licencias cargadas desde BD: {sum(len(v) for v in database.LAR.values())} LAR, {sum(len(v) for v in database.LPP.values())} LPP")

    df_personal = pd.DataFrame(PERSONAL)
    df_personal['Horas_Fijas_Semanales'] = df_personal['Asignaciones_Fijas'].apply(calcular_horas_fijas)

    database.sincronizar_personal(df_personal)

    # Cargar acumulados históricos desde la BD (todo anterior a FECHA_INICIO)
    historial = database.cargar_historial(df_personal, FECHA_INICIO)
    for campo in ['Horas_Anuales_Previas', 'Findes_Semanas_Previos', 'Findes_Habiles_Previos',
                  'Findes_Largos_3_Previos', 'Findes_Largos_4_Previos']:
        df_personal[campo] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get(campo, 0))

    print("📊 Historial cargado desde la BD:")
    for _, p in df_personal.iterrows():
        print(f"   {p['Nombre']:<22} {p['Horas_Anuales_Previas']:>4}hs acum | "
              f"Finde: {p['Findes_Semanas_Previos']}/{p['Findes_Habiles_Previos']} | "
              f"FL3: {p['Findes_Largos_3_Previos']} FL4: {p['Findes_Largos_4_Previos']}")

    # --- VALIDACIÓN DEL RANGO DE FECHAS ---
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")

    if fecha_fin_dt < fecha_inicio_dt:
        raise ValueError(f"Error: FECHA_FIN ({FECHA_FIN}) es anterior a FECHA_INICIO ({FECHA_INICIO}).")

    # +1 porque ambas fechas son inclusive
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1

    if total_dias % 7 != 0:
        raise ValueError(
            f"Error: el rango {FECHA_INICIO} → {FECHA_FIN} tiene {total_dias} días. "
            f"Deben introducirse semanas completas (múltiplo de 7 días)."
        )

    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = DIAS_DEL_BLOQUE // 7

    print(f"Periodo: {FECHA_INICIO} -> {FECHA_FIN} ({num_semanas} semanas / {DIAS_DEL_BLOQUE} días)")

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    print("Construyendo el modelo de optimización...")
    offset_dia = fecha_inicio_dt.weekday()
    modelo, turnos = construir_modelo(df_personal, DEMANDA_TURNOS, DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas)

    df_resultados = resolver_modelo(modelo, turnos, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia)

    if df_resultados is not None:
        df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados)
        df_reporte = generar_reporte(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, num_semanas)
        exportar_excel(df_pivot, df_reporte, fechas_unicas)

        # --- ACEPTAR Y GUARDAR EN BD ---
        print("\n" + "═" * 55)
        print("  ¿Aceptar y guardar este cronograma en la base de datos?")
        print("  (El Excel ya fue generado. Esto solo persiste los datos)")
        print("═" * 55)
        resp = input("  Respuesta (s/n): ").strip().lower()
        if resp == 's':
            database.guardar_cronograma(
                df_resultados, df_personal,
                FECHA_INICIO, FECHA_FIN,
                feriados_indices, offset_dia, DIAS_DEL_BLOQUE
            )
            print("\n✅ Cronograma guardado. La próxima generación usará estos datos como historial.")
        else:
            print("\n⏭  Cronograma NO guardado en la BD.")

if __name__ == "__main__":
    main()
