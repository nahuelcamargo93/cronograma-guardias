import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

nombres_buscar = [
    "Arias Guillermina",
    "Kolarik Jorge Luis",
    "Silva, Martín Enrique",
    "Mora, Sergio Enrique",
    "Nesteruk María Silvia",
    "Pregot Analia Mariana",
    "Quiroga Sassu Maria Macarena",
    "Zeballos Valeria Alejandra",
    "Palermo Agustín",
    "Matricadi Wendy Ailen",
    "Villegas Oliva Maria Belén"
]

print("--- TODOS LOS NOMBRES EN SERVICIO 3 ---")
rows_all = cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 3").fetchall()
nombres_db = [r[0] for r in rows_all]
for n in sorted(nombres_db):
    print(f"  {n}")

print("\n--- BUSCANDO CON COMPARACION FLEXIBLE ---")
import re
def normalize(s):
    # quitar acentos y caracteres raros
    s = s.lower()
    s = re.sub(r'[áäâà]', 'a', s)
    s = re.sub(r'[éëêè]', 'e', s)
    s = re.sub(r'[íïîì]', 'i', s)
    s = re.sub(r'[óöôò]', 'o', s)
    s = re.sub(r'[úüûù]', 'u', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

for nom in nombres_buscar:
    nom_norm = normalize(nom)
    encontrados = []
    for db_nom in nombres_db:
        db_nom_norm = normalize(db_nom)
        # Ver si se parecen (si el nombre buscado está en el de DB o viceversa, o palabras comunes)
        if nom_norm in db_nom_norm or db_nom_norm in nom_norm:
            encontrados.append(db_nom)
    print(f"Buscando: {nom}")
    if encontrados:
        for enc in encontrados:
            print(f"  [POSIBLE] {enc}")
    else:
        # buscar por primer apellido o primer nombre
        parts = re.split(r'[\s,]+', nom)
        sub_enc = []
        for part in parts:
            if len(part) < 3: continue
            part_norm = normalize(part)
            for db_nom in nombres_db:
                if part_norm in normalize(db_nom):
                    sub_enc.append(db_nom)
        sub_enc = list(set(sub_enc))
        if sub_enc:
            for enc in sub_enc:
                print(f"  [PARCIAL] {enc}")
        else:
            print("  [NOT FOUND]")

conn.close()
