import sqlite3
import sys
import os

# Asegurar path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.schema import inicializar_db

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Poner a NULL horas reglamentarias de personal
    print("Estableciendo horas reglamentarias de personal a NULL...")
    cursor.execute("UPDATE personal SET horas_mensuales_reglamentarias = NULL")
    
    # 2. Activar a Barloa, Godoy y Quintero
    print("Activando a Barloa, Godoy y Quintero...")
    cursor.execute("UPDATE personal SET activo = 1 WHERE nombre LIKE '%Barloa%' OR nombre LIKE '%Godoy, Maria%' OR nombre LIKE '%Quintero%'")
    
    conn.commit()
    
    # 3. Correr inicializacion de DB para registrar SOLO_ASIGNACIONES_FIJAS en catalogo
    print("Inicializando base de datos para registrar nueva regla en catalogo...")
    inicializar_db()
    
    # 4. Asignar la regla SOLO_ASIGNACIONES_FIJAS en personal_reglas para Barloa, Godoy y Quintero
    # Buscamos sus nombres exactos en la DB
    cursor = conn.cursor()
    nombres = cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE '%Barloa%' OR nombre LIKE '%Godoy, Maria%' OR nombre LIKE '%Quintero%'").fetchall()
    
    for (nom,) in nombres:
        print(f"Asignando regla SOLO_ASIGNACIONES_FIJAS a {nom}...")
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
            VALUES (?, 'SOLO_ASIGNACIONES_FIJAS', '{}', 1)
            ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET activo = 1, parametros_json = '{}'
        """, (nom,))
        
    conn.commit()
    
    # Verificar cambios
    print("\n--- PERSONAL ACTIVO SERVICIO 3 ---")
    personal = cursor.execute("SELECT nombre, activo FROM personal WHERE servicio_id = 3 AND activo = 1").fetchall()
    for nom, act in personal:
        print(f"  - {nom} (Activo: {act})")
        
    print("\n--- REGLAS SOLO_ASIGNACIONES_FIJAS ASIGNADAS ---")
    reglas = cursor.execute("SELECT personal_nombre, codigo_regla, activo FROM personal_reglas WHERE codigo_regla = 'SOLO_ASIGNACIONES_FIJAS'").fetchall()
    for row in reglas:
        print(f"  - {row[0]}: {row[1]} (Activo: {row[2]})")
        
    conn.close()

if __name__ == "__main__":
    main()
