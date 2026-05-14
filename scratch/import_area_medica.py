import sqlite3
import pandas as pd
import json
import re
import math

def format_metadata(text):
    if pd.isna(text) or str(text).strip() == "":
        return None
    
    # Try to parse "año 2026, tramo 2"
    data = {}
    text = str(text).replace("\n", " ").lower()
    
    anio_match = re.search(r"(año|anio)[:\s]+(\d{4})", text)
    if anio_match:
        data["anio"] = int(anio_match.group(2))
    
    tramo_match = re.search(r"tramo\s+(\d+)", text)
    if tramo_match:
        data["tramo"] = int(tramo_match.group(1))
        
    if not data:
        data["detalle"] = text.strip()
        
    return json.dumps(data, ensure_ascii=False)

def run_import():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    SERVICIO_ID = 3
    ORGANIZACION_ID = 1
    
    print(f"--- Setting up Service {SERVICIO_ID} (Area Medica UTI) ---")
    
    # 1. Puestos
    cursor.execute("DELETE FROM puestos WHERE servicio_id = ?", (SERVICIO_ID,))
    cursor.execute("INSERT INTO puestos (servicio_id, nombre) VALUES (?, ?)", (SERVICIO_ID, "Planta"))
    id_planta = cursor.lastrowid
    cursor.execute("INSERT INTO puestos (servicio_id, nombre) VALUES (?, ?)", (SERVICIO_ID, "Residente"))
    id_residente = cursor.lastrowid
    print(f"Puestos created: Planta ({id_planta}), Residente ({id_residente})")
    
    # 2. Turnos Config
    cursor.execute("DELETE FROM turnos_config WHERE servicio_id = ?", (SERVICIO_ID,))
    turnos = [
        ("G", "08:00", 24, 1),
        ("D", "08:00", 12, 2),
        ("N", "20:00", 12, 3)
    ]
    
    for p_id, p_name in [(id_planta, "Planta"), (id_residente, "Residente")]:
        for nombre, inicio, horas, orden in turnos:
            full_name = f"{nombre}_{p_name}"
            cursor.execute("""
                INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, orden, activo, dias_semana, puesto_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (SERVICIO_ID, full_name, inicio, horas, orden, 1, '0,1,2,3,4,5,6', p_id))
    print("Turnos created for both roles (with unique names).")
    
    # 3. Demanda Config
    cursor.execute("DELETE FROM demanda_config WHERE puesto_id IN (?, ?)", (id_planta, id_residente))
    slots = [
        ("08:00", "14:00"),
        ("14:00", "20:00"),
        ("20:00", "02:00"),
        ("02:00", "08:00")
    ]
    
    for tipo_dia in ["Semana", "Finde_Feriado"]:
        # Planta: 3-5
        for start, end in slots:
            cursor.execute("""
                INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador, cantidad_min, cantidad_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_planta, tipo_dia, start, end, 3, '>=', 3, 5))
            
        # Residente: 1-3
        for start, end in slots:
            cursor.execute("""
                INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador, cantidad_min, cantidad_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_residente, tipo_dia, start, end, 1, '>=', 1, 3))
    print("Demanda config set (4 slots of 6hs to cover 24hs).")
    
    # 4. Service Rules
    cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = ?", (SERVICIO_ID,))
    # Rule 174: Penalty for D and N
    penalties = [
        {"turno": "D_Planta", "peso": 1000},
        {"turno": "N_Planta", "peso": 1000},
        {"turno": "D_Residente", "peso": 1000},
        {"turno": "N_Residente", "peso": 1000}
    ]
    cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                   (SERVICIO_ID, 174, json.dumps(penalties)))
    # Rule 167: 12h rest
    cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                   (SERVICIO_ID, 167, json.dumps({"horas": 12})))
    print("Service rules added (Penalty for D/N, 12h rest).")
    
    # 5. Import Personnel
    print("\n--- Importing Personnel from Excel ---")
    df = pd.read_excel('Personal medico (con LAR y LPP).xlsx')
    
    # Clean previous personal for this service
    cursor.execute("DELETE FROM personal WHERE servicio_id = ?", (SERVICIO_ID,))
    
    for idx, row in df.iterrows():
        nombre = str(row['Nombre']).strip()
        if nombre == "nan" or not nombre:
            continue
            
        rol = str(row['Categoria']).strip()
        # Ensure role matches puesto name for the solver logic
        if "Residente" in rol:
            rol = "Residente"
        else:
            rol = "Planta"
            
        # Insert personal
        cursor.execute("""
            INSERT INTO personal (nombre, rol, organizacion_id, servicio_id)
            VALUES (?, ?, ?, ?)
        """, (nombre, rol, ORGANIZACION_ID, SERVICIO_ID))
        
        # Prohibited turns (Rule 4)
        prohibido = str(row.get('Turno prohbido', '')).strip()
        if "24hs" in prohibido or "G" in prohibido:
            # Prohibit both variants to be sure, or just the one for the role
            turno_to_exclude = f"G_{rol}"
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
                VALUES (?, ?, ?)
            """, (nombre, 4, json.dumps({"turnos": [turno_to_exclude]})))
            
        # Licencias LPP
        if not pd.isna(row['Fechia inicio LPP']):
            inicio = pd.to_datetime(row['Fechia inicio LPP']).strftime('%Y-%m-%d')
            fin = pd.to_datetime(row['Fecha fin LPP']).strftime('%Y-%m-%d')
            meta = format_metadata(row['Metadata LPP'])
            cursor.execute("""
                INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, "LPP", inicio, fin, meta))
            
        # Licencias LAR
        if not pd.isna(row['Fecha inicio LAR']):
            inicio = pd.to_datetime(row['Fecha inicio LAR']).strftime('%Y-%m-%d')
            fin = pd.to_datetime(row['Fecha Fin LAR']).strftime('%Y-%m-%d')
            meta = format_metadata(row['Metadata LAR'])
            cursor.execute("""
                INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, "LAR", inicio, fin, meta))
            
    print(f"Imported {len(df)} rows from Excel.")
    
    conn.commit()
    conn.close()
    print("\n--- Import Process Finished ---")

if __name__ == "__main__":
    run_import()
