import sqlite3
import json

def list_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== Reglas en Catalogo relacionadas con Licencia o Credito ===")
    cursor.execute("""
        SELECT id, codigo_regla, tipo, descripcion 
        FROM reglas_catalogo 
        WHERE codigo_regla LIKE '%LICENCIA%' OR codigo_regla LIKE '%CREDITO%';
    """)
    for r in cursor.fetchall():
        print(f"ID: {r[0]} | Codigo: {r[1]} | Tipo: {r[2]} | Desc: {r[3]}")
        
    print("\n=== Configuracion de CREDITO_HORARIO_LICENCIA por servicio ===")
    cursor.execute("""
        SELECT sr.servicio_id, s.nombre, sr.parametros_json, sr.activo 
        FROM servicios_reglas sr
        JOIN servicios s ON sr.servicio_id = s.id
        WHERE sr.codigo_regla = 'CREDITO_HORARIO_LICENCIA';
    """)
    for r in cursor.fetchall():
        print(f"Servicio ID: {r[0]} ({r[1]}) | Activo: {r[3]} | Params: {r[2]}")
        
    conn.close()

if __name__ == "__main__":
    list_rules()
