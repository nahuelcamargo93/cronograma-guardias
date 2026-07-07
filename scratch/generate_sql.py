import sqlite3
import json
import re

user_data = [
    {"nombre": "FERNANDEZ Celeste Ivana", "rol": "", "categoria": "A", "turno": "00-06"},
    {"nombre": "FERNANDEZ Juan Emir", "rol": "Supervisor suplente", "categoria": "A", "turno": "00-06"},
    {"nombre": "GIMENEZ Adriana", "rol": "", "categoria": "A", "turno": "00-06"},
    {"nombre": "OLGUIN ALDECO Jennifer Sofia", "rol": "Supervisor Titular", "categoria": "A", "turno": "00-06"},
    {"nombre": "ESCUDERO Gabriela", "rol": "", "categoria": "A", "turno": "00-06"},
    {"nombre": "VILLEGAS Angel", "rol": "", "categoria": "A", "turno": "00-06"},
    {"nombre": "ROMERO Tomas", "rol": "Supervisor Titular", "categoria": "A", "turno": "00-06"},
    {"nombre": "SUÑER, Mara", "rol": "", "categoria": "A", "turno": "00-06"},
    {"nombre": "ALCARAZ Xavier", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "OJEDA Miriam", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "RUOCCO MUÑOZ Luis Alfredo", "rol": "Supervisor Suplente", "categoria": "B", "turno": "06-12"},
    {"nombre": "STEIMBRECHER Yolanda", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "LEDESMA PAZ Micaela", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "MANSILLA Diego", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "MESSINA Eduardo", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "RODRIGUEZ Maximiliano", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "SANCIO Paola", "rol": "Supervisor Titular", "categoria": "B", "turno": "06-12"},
    {"nombre": "FLORES José Nicolás", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "FERNANDEZ Claudia Elizabeth", "rol": "", "categoria": "B", "turno": "06-12"},
    {"nombre": "BARROSO Alan", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "BRIZUELA Irma", "rol": "Supervisor Suplente", "categoria": "C", "turno": "12-18"},
    {"nombre": "GUERRERO Cesar", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "MOCDESE Marcelo Leonel", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "TORRES Yesica", "rol": "Supervisor Titular", "categoria": "C", "turno": "12-18"},
    {"nombre": "VERGARA Nazareno", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "CANO Avril", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "FUNEZ Valeria Vanesa", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "VILLEGAS Gaston", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "QUINTANA Felipe Gabriel", "rol": "Supervisor Suplente", "categoria": "D", "turno": "18-24"},
    {"nombre": "MIRANDA Luis", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "MUÑOZ Maria Carolina", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "SUAREZ Carolina", "rol": "Supervisor Titular", "categoria": "D", "turno": "18-24"},
    {"nombre": "VELEZ Facundo", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "VERGARA Mariano", "rol": "", "categoria": "D", "turno": "18-24"},
]

def normalize(name):
    n = name.upper().strip()
    n = n.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    n = n.replace("Ü", "U").replace("Ñ", "N")
    n = re.sub(r'[^A-Z\s]', '', n)
    n = " ".join(n.split())
    return n

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Mapear nombres a BD
db_personal = cursor.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 4").fetchall()
db_mapped = {normalize(row[0]): row for row in db_personal}

# Nombre del puesto
puestos_validos = {31: "Supervisor", 32: "Monitorista", 33: "Administrativo"}

turnos_excluir_map = {
    "A": ["06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "Administrativo"],
    "B": ["00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor", "00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "Administrativo"],
    "C": ["00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor", "00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "Administrativo"],
    "D": ["00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "Administrativo"]
}

updates_personal = []
updates_puestos = []
updates_exclusiones = []

print("--- ANALIZANDO CAMBIOS ---")

for u in user_data:
    norm_name = normalize(u["nombre"])
    
    # Manejar caso SUÑER Mara Tatiana manualmente si hace falta
    if norm_name == "SUNER MARA":
        norm_name = "SUNER MARA TATIANA"
        
    if norm_name not in db_mapped:
        print(f"ERROR: No se encontró en la BD a: {u['nombre']}")
        continue
        
    db_name, db_cat, db_rol, db_act = db_mapped[norm_name]
    
    # 1. Cambios en personal
    nuevo_rol = u["rol"] if u["rol"] else "Monitorista"
    nueva_cat = u["categoria"]
    
    if db_cat != nueva_cat or db_rol != nuevo_rol or db_act != 1:
        updates_personal.append({
            "nombre": db_name,
            "cat_vieja": db_cat,
            "cat_nueva": nueva_cat,
            "rol_viejo": db_rol,
            "rol_nuevo": nuevo_rol,
            "sql": f"UPDATE personal SET categoria = '{nueva_cat}', rol = '{nuevo_rol}', activo = 1 WHERE nombre = '{db_name}';"
        })
        
    # 2. Cambios en puestos
    es_supervisor = "supervisor" in nuevo_rol.lower()
    puesto_deseado = 31 if es_supervisor else 32
    
    actuales_puestos = [r[0] for r in cursor.execute("SELECT puesto_id FROM personal_puestos WHERE personal_nombre = ?", (db_name,)).fetchall()]
    
    if puesto_deseado not in actuales_puestos or len(actuales_puestos) > 1:
        updates_puestos.append({
            "nombre": db_name,
            "puestos_actuales": [puestos_validos.get(pid, pid) for pid in actuales_puestos],
            "puesto_deseado": puestos_validos[puesto_deseado],
            "sql_delete": f"DELETE FROM personal_puestos WHERE personal_nombre = '{db_name}';",
            "sql_insert": f"INSERT INTO personal_puestos (personal_nombre, puesto_id, es_primario, servicio_id) VALUES ('{db_name}', {puesto_deseado}, 1, 4);"
        })
        
    # 3. Cambios en exclusiones de turnos
    turnos_excluidos = turnos_excluir_map[nueva_cat]
    params_json = json.dumps([{"turnos": turnos_excluidos, "dias": [0, 1, 2, 3, 4, 5, 6]}], indent=2)
    
    # Buscar si ya existe la regla EXCLUIR_TURNOS
    exc_actuales = cursor.execute("SELECT id, parametros_json FROM personal_reglas_ajustes WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS' AND activo = 1", (db_name,)).fetchall()
    
    debe_insertar = True
    if exc_actuales:
        debe_insertar = False
        # Si ya existe pero difieren los parámetros
        for eid, e_params in exc_actuales:
            try:
                parsed_actual = json.loads(e_params)
                # Ordenar listas para comparar
                if parsed_actual and isinstance(parsed_actual, list) and "turnos" in parsed_actual[0]:
                    t_act = sorted(parsed_actual[0]["turnos"])
                    t_des = sorted(turnos_excluidos)
                    if t_act != t_des:
                        updates_exclusiones.append({
                            "nombre": db_name,
                            "tipo": "UPDATE",
                            "excluidos_deseados": turnos_excluidos,
                            "sql": f"UPDATE personal_reglas_ajustes SET parametros_json = '{params_json}' WHERE id = {eid};"
                        })
            except:
                updates_exclusiones.append({
                    "nombre": db_name,
                    "tipo": "UPDATE_CORRUPTO",
                    "excluidos_deseados": turnos_excluidos,
                    "sql": f"UPDATE personal_reglas_ajustes SET parametros_json = '{params_json}' WHERE id = {eid};"
                })
    
    if debe_insertar:
        updates_exclusiones.append({
            "nombre": db_name,
            "tipo": "INSERT",
            "excluidos_deseados": turnos_excluidos,
            "sql": f"INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id) VALUES ('{db_name}', 'EXCLUIR_TURNOS', '2026-06-01', '2026-12-31', 'SOBRESCRIBIR', '{params_json}', 1, 4);"
        })

print(f"\nTotal cambios en Personal: {len(updates_personal)}")
for u in updates_personal:
    print(f"  - {u['nombre']}: Cat {u['cat_vieja']} -> {u['cat_nueva']}, Rol '{u['rol_viejo']}' -> '{u['rol_nuevo']}'")

print(f"\nTotal cambios en Puestos: {len(updates_puestos)}")
for u in updates_puestos:
    print(f"  - {u['nombre']}: Puestos {u['puestos_actuales']} -> {u['puesto_deseado']}")

print(f"\nTotal cambios en Exclusiones: {len(updates_exclusiones)}")
for u in updates_exclusiones:
    print(f"  - {u['nombre']} ({u['tipo']})")

# Escribir todas las queries a un archivo para que el usuario pueda revisarlas
with open("scratch/aplicar_cambios.sql", "w", encoding="utf-8") as f:
    f.write("-- QUERIES DE ACTUALIZACION DE PERSONAL --\n")
    for u in updates_personal:
        f.write(u["sql"] + "\n")
    f.write("\n-- QUERIES DE ACTUALIZACION DE PUESTOS --\n")
    for u in updates_puestos:
        f.write(u["sql_delete"] + "\n")
        f.write(u["sql_insert"] + "\n")
    f.write("\n-- QUERIES DE ACTUALIZACION DE EXCLUSIONES DE TURNOS --\n")
    for u in updates_exclusiones:
        f.write(u["sql"] + "\n")

conn.close()
print("\n[OK] Queries de cambio escritas en scratch/aplicar_cambios.sql")
