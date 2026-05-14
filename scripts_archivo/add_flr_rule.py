import sqlite3

def add_flr_rule():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Check if rule exists
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'")
    res = cursor.fetchone()
    if res:
        regla_id = res[0]
        print(f"Rule already exists with ID: {regla_id}")
    else:
        cursor.execute("INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES ('FINDE_LARGO_REGLAMENTARIO', 'HARD', 'Fuerza exactamente 1 finde largo reglamentario (Sab, Dom, Lun, Mar libres) por bloque')")
        regla_id = cursor.lastrowid
        print(f"Rule created with ID: {regla_id}")
        
    # Check if service has this rule
    cursor.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", (regla_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json, activo) VALUES (2, ?, '{\"cantidad\": 1}', 1)", (regla_id,))
        print("Rule assigned to Enfermeria UTI with cantidad: 1")
    else:
        print("Rule already assigned to service.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_flr_rule()
