import sqlite3

def add_flr_rule():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Add to catalog
    print("Adding FINDE_LARGO_REGLAMENTARIO to catalog...")
    cursor.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('FINDE_LARGO_REGLAMENTARIO', 'HARD', 'Un bloque de 4 dias libres (Sab-Mar) por mes obligatorio');
    """)
    rule_id = cursor.lastrowid
    print(f"Rule added with ID: {rule_id}")
    
    # 2. Add to service 2
    print("Adding FLR to service 2...")
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json)
        VALUES (?, ?, ?);
    """, (2, rule_id, '{"cantidad": 1}'))
    
    conn.commit()
    print("FLR rule and service configuration added successfully.")
    conn.close()

if __name__ == "__main__":
    add_flr_rule()
