import sqlite3
import pandas as pd

def analyze():
    conn = sqlite3.connect('cronograma_inteligente.db')
    name = 'CORSO ARTURO'
    
    print("--- PERSONAL DATA ---")
    pers = pd.read_sql(f"SELECT * FROM personal WHERE nombre = '{name}'", conn)
    print(pers)
    
    print("\n--- REGLAS ASIGNADAS AL PERSONAL (personal_reglas) ---")
    p_rules = pd.read_sql(f"""
        SELECT rc.codigo_regla, pr.parametros_json 
        FROM personal_reglas pr
        JOIN reglas_catalogo rc ON pr.regla_id = rc.id
        WHERE pr.personal_nombre = '{name}'
    """, conn)
    print(p_rules)

    print("\n--- AJUSTES REGLAS PERSONAL (personal_reglas_ajustes) ---")
    ajustes = pd.read_sql(f"SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = '{name}'", conn)
    print(ajustes)
    
    conn.close()

if __name__ == "__main__":
    analyze()
