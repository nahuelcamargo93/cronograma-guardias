import sys
import os
import pandas as pd
import datetime
from datetime import date, timedelta
import sqlite3

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import queries as db_queries
from database.connection import get_connection

# Configuración
FILE_NAME = "para_importar_kineJunio.xlsx"
SERVICIO_ID = 1
FECHA_INICIO = "2026-05-25"
FECHA_FIN = "2026-06-21"
NOTAS = "Importado desde para_importar_kineJunio.xlsx (aprobado)"

import unicodedata

def limpiar_string(s):
    if not isinstance(s, str):
        return ""
    # Normalizar codificaciones corruptas comunes
    s = s.replace("í­", "i").replace("í", "i")
    s = s.replace("Lic.", "").replace("Lic", "").strip()
    # Remover acentos/tildes
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower()

def buscar_nombre_oficial(nombre_excel, db_names):
    n_excel_clean = limpiar_string(nombre_excel)
    
    # Intentar buscar por coincidencia en el apellido
    for db_name in db_names:
        apellido_db = db_name.split(",")[0].strip()
        apellido_db_clean = limpiar_string(apellido_db)
        
        # Si el apellido de la BD está en el nombre del Excel, o viceversa
        if apellido_db_clean in n_excel_clean or n_excel_clean in apellido_db_clean:
            return db_name
            
    # Caso especial para "Giacoppo" / "Giaccoppo"
    if "giacco" in n_excel_clean or "giacop" in n_excel_clean:
        for db_name in db_names:
            if "giacop" in db_name.lower():
                return db_name
                
    # Caso especial para "Guardia" / "Guardía"
    if "guard" in n_excel_clean:
        for db_name in db_names:
            if "guard" in db_name.lower():
                return db_name

    return None


def run():
    print(f"--- Iniciando importación del archivo: {FILE_NAME} ---")
    if not os.path.exists(FILE_NAME):
        print(f"Error: El archivo {FILE_NAME} no existe.")
        return

    # 1. Leer Excel y normalizar columnas de fechas
    df_raw = pd.read_excel(FILE_NAME)
    print(f"Excel cargado. Columnas totales: {len(df_raw.columns)}")

    # Identificar columnas que correspondan a fechas
    date_cols = []
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(FECHA_FIN, "%Y-%m-%d")

    for col in df_raw.columns:
        if col == 'Turno':
            continue
        try:
            col_dt = pd.to_datetime(col)
            if fecha_inicio_dt <= col_dt <= fecha_fin_dt:
                date_cols.append(col)
        except Exception:
            pass

    date_cols = sorted(date_cols, key=lambda x: pd.to_datetime(x))
    print(f"Columnas en el rango a importar ({FECHA_INICIO} -> {FECHA_FIN}): {len(date_cols)}")
    if len(date_cols) != 28:
        print(f"Advertencia: Se esperaban 28 días, pero se encontraron {len(date_cols)} columnas.")

    # Obtener personal oficial de la BD para mapeo
    db_personal_list = db_queries.obtener_personal_db(SERVICIO_ID)
    db_names = [p['Nombre'] for p in db_personal_list]
    print(f"Personal registrado en BD para el servicio 1 ({len(db_names)} integrantes): {db_names}")

    # 2. Procesar asignaciones día por día
    resultados = []
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    for col in date_cols:
        col_dt = pd.to_datetime(col)
        fecha_str = col_dt.strftime("%Y-%m-%d")
        dia_semana_str = dias_nombres[col_dt.weekday()]

        for idx, row in df_raw.iterrows():
            turno_raw = str(row['Turno']).strip()
            # Normalizar turno (corregir codificación si es necesario)
            turno = turno_raw.replace('Maana', 'Mañana')
            
            persona_raw = row[col]
            if pd.isna(persona_raw):
                continue
                
            persona_raw = str(persona_raw).strip()
            if not persona_raw or persona_raw.lower() in ('nan', 'none', ''):
                continue

            # Mapear nombre de personal dinámicamente
            nombre_oficial = buscar_nombre_oficial(persona_raw, db_names)
            if not nombre_oficial:
                raise ValueError(
                    f"ERROR: No se pudo mapear el nombre '{persona_raw}' del Excel a ningún "
                    f"integrante del personal en la BD. Por favor verifique el nombre y reintente."
                )
            
            resultados.append({
                "Fecha": fecha_str,
                "Dia_Semana": dia_semana_str,
                "Turno": turno,
                "Personal": nombre_oficial
            })

    df_resultados = pd.DataFrame(resultados)
    print(f"Total de asignaciones leídas y procesadas exitosamente: {len(df_resultados)}")

    # 3. Preparar variables para guardar_cronograma
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()

    # Obtener feriados para calcular índices
    feriados_db = db_queries.obtener_feriados(FECHA_INICIO, FECHA_FIN, servicio_id=SERVICIO_ID)
    feriados_indices = []
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    # Convertir lista a DataFrame
    df_personal = pd.DataFrame(db_personal_list)

    
    # Asegurar columnas correctas para df_personal en guardar_cronograma
    # db_queries.guardar_cronograma espera un df_personal
    
    # 4. Limpieza previa del rango de fechas (Idempotencia)
    print(f"Limpiando cualquier cronograma previo existente en el rango {FECHA_INICIO} -> {FECHA_FIN} para Kinesiologia...")
    with get_connection() as conn:
        # Buscar IDs de cronogramas en ese rango que tengan guardias de kinesiologia (servicio 1)
        cur_old = conn.execute("""
            SELECT DISTINCT c.id FROM cronogramas c
            JOIN guardias g ON c.id = g.cronograma_id
            JOIN personal p ON g.nombre = p.nombre
            WHERE c.fecha_inicio = ? AND c.fecha_fin = ? AND p.servicio_id = ?
        """, (FECHA_INICIO, FECHA_FIN, SERVICIO_ID))
        old_ids = [r[0] for r in cur_old.fetchall()]
        
        for oid in old_ids:
            print(f"Eliminando cronograma anterior ID {oid}...")
            conn.execute("DELETE FROM cronogramas WHERE id = ?", (oid,))
            
    # 5. Guardar en BD (estado inicial borrador)
    print("Persistiendo cronograma en base de datos...")
    cronograma_id = db_queries.guardar_cronograma(
        df_resultados, df_personal,
        FECHA_INICIO, FECHA_FIN,
        feriados_indices, offset_dia, dias_del_bloque,
        notas=NOTAS
    )

    # 6. Marcar como aprobado
    print(f"Marcando cronograma ID {cronograma_id} como 'aprobado'...")
    with get_connection() as conn:
        conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = ?", (cronograma_id,))
    print(f"[OK] Cronograma ID {cronograma_id} aprobado exitosamente.")

    # 7. Generar el Reporte Excel Oficial
    print("Generando reporte Excel premium de Kinesiologia...")
    # Calcular num_semanas
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    # Cargar config_turnos
    config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )

    try:
        from reportes.servicio_1_kinesiologia.kinesiologia import generar_y_exportar as gen_kin
        gen_kin(
            df_resultados, df_personal, dias_del_bloque, feriados_indices,
            FECHA_INICIO, offset_dia, config_turnos, num_semanas,
            crono_id=cronograma_id
        )
        print("[OK] Reporte Excel premium generado con exito.")
    except Exception as e:
        print(f"[ERROR] Error al generar reporte Excel: {e}")


if __name__ == '__main__':
    run()
