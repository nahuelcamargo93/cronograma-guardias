import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

def get_regla_id(codigo):
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (codigo,))
    row = cursor.fetchone()
    return row[0] if row else None

id_excluir = get_regla_id('EXCLUIR_TURNOS')
id_fija = get_regla_id('ASIGNACION_FIJA')

# 1. Lista de todo el personal
cursor.execute("SELECT nombre FROM personal")
todos = [r[0] for r in cursor.fetchall()]

permitidos_especial = ['Lic. Coniglio', 'Lic. Giaccoppo', 'Lic. Camargo N.']

# 2. Actualizar EXCLUIR_TURNOS para todos
# Primero recuperamos lo que ya tienen para no borrarlo (ej: Toledo ya tenia bloqueado UTI)
for nombre in todos:
    cursor.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = ? AND regla_id = ?", (nombre, id_excluir))
    row = cursor.fetchone()
    
    turnos_bloqueados = []
    if row and row[0]:
        try:
            actual = json.loads(row[0])
            if isinstance(actual, list) and len(actual) > 0:
                turnos_bloqueados = actual[0].get('turnos', [])
        except: pass

    # Si NO está en la lista de permitidos, le agregamos los especiales
    if nombre not in permitidos_especial:
        for t in ["Mañana_especial", "Tarde_especial"]:
            if t not in turnos_bloqueados:
                turnos_bloqueados.append(t)
    
    # Aplicar la actualización
    if turnos_bloqueados:
        params = json.dumps([{"turnos": turnos_bloqueados, "dias": [0,1,2,3,4,5,6]}])
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
            VALUES (?, ?, ?)
            ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
        """, (nombre, id_excluir, params))

# 3. Corregir Camargo a Tarde Especial
asig_camargo = json.dumps([
    {"Dia": "Lunes", "Turno": "Tarde_especial", "Tipo": "Especial", "Horas": 6},
    {"Dia": "Miercoles", "Turno": "Tarde", "Tipo": "Asistencial", "Horas": 6},
    {"Dia": "Viernes", "Turno": "Tarde", "Tipo": "Asistencial", "Horas": 6}
])
cursor.execute("UPDATE personal_reglas SET parametros_json = ? WHERE personal_nombre = ? AND regla_id = ?", 
               (asig_camargo, 'Lic. Camargo N.', id_fija))

conn.commit()
conn.close()
print("Base de datos actualizada: Especiales bloqueados por exclusion general y Camargo corregido.")
