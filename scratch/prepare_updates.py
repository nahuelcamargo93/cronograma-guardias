import sqlite3
import json
import re

# Datos proveídos por el usuario
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
    {"nombre": "FERNANDEZ Claudia Elizabeth", "rol": "", "categoria": "B", "turno": "06 - 12"},
    {"nombre": "BARROSO Alan", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "BRIZUELA Irma", "rol": "Supervisor Suplente", "categoria": "C", "turno": "12-18"},
    {"nombre": "GUERRERO Cesar", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "MOCDESE Marcelo Leonel", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "TORRES Yesica", "rol": "Supervisor Titular", "categoria": "C", "turno": "12-18"},
    {"nombre": "VERGARA Nazareno", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "CANO Avril", "rol": "", "categoria": "C", "turno": "12-18"},
    {"nombre": "FUNEZ Valeria Vanesa", "rol": "Monitorista", "categoria": "D", "turno": "18-24"},
    {"nombre": "VILLEGAS Gaston", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "QUINTANA Felipe Gabriel", "rol": "Supervisor Suplente", "categoria": "D", "turno": "18-24"},
    {"nombre": "MIRANDA Luis", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "MUÑOZ Maria Carolina", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "SUAREZ Carolina", "rol": "Supervisor Titular", "categoria": "D", "turno": "18-24"},
    {"nombre": "VELEZ Facundo", "rol": "", "categoria": "D", "turno": "18-24"},
    {"nombre": "VERGARA Mariano", "rol": "", "categoria": "D", "turno": "18-24"},
]

def normalize(name):
    # Reemplazar acentos y caracteres raros
    n = name.upper().strip()
    n = n.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    n = n.replace("Ü", "U").replace("Ñ", "N")
    n = re.sub(r'[^A-Z\s]', '', n) # Quitar comas, etc.
    n = " ".join(n.split())
    return n

# Normalizar nombres del usuario para matchear con la BD
user_map = {}
for u in user_data:
    norm = normalize(u["nombre"])
    user_map[norm] = u

# Conectar a la base de datos
conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Cargar personal actual del servicio 4
db_personal = cursor.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 4").fetchall()

print("--- ANÁLISIS DE MATCHING ---")
matched_count = 0
unmatched_db = []
unmatched_user = list(user_map.keys())

db_mapped = {} # norm_name: row
for row in db_personal:
    db_name, db_cat, db_rol, db_act = row
    norm_db = normalize(db_name)
    db_mapped[norm_db] = row
    
    # Intentar hacer match parcial si no es exacto
    matched = False
    for u_norm in list(unmatched_user):
        # Match exacto o si una parte significativa coincide
        if u_norm == norm_db or (len(u_norm) > 10 and (u_norm in norm_db or norm_db in u_norm)):
            matched_count += 1
            unmatched_user.remove(u_norm)
            matched = True
            # Guardamos mapeo
            user_map[u_norm]["db_name"] = db_name
            user_map[u_norm]["matched"] = True
            break
    if not matched:
        unmatched_db.append(row)

print(f"Coincidencias exactas/cercanas: {matched_count}/{len(user_data)}")
print("No encontrados en la BD (se asume que se deben crear o renombrar):", unmatched_user)
print("Encontrados en la BD pero no en la lista del usuario (se asume inactivar o verificar):", unmatched_db)

conn.close()
