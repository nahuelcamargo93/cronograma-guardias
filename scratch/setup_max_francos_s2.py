import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Insertar en reglas_catalogo
    regla_codigo = "MAX_FRANCOS_SEMANA"
    regla_tipo = "HARD"
    regla_desc = "Límite máximo de francos por semana calendario"

    cursor.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES (?, ?, ?)
    """, (regla_codigo, regla_tipo, regla_desc))
    print(f"Regla {regla_codigo} insertada en el catálogo (si no existía).")

    # 2. Configurar y Activar la regla para el Servicio 2 (Enfermería, ID 2)
    servicio = cursor.execute("SELECT id, nombre FROM servicios WHERE id = 2").fetchone()
    if servicio:
        print(f"Servicio encontrado: {servicio[1]} (ID: {servicio[0]})")
        
        # Insertar o actualizar para activar
        params = {"limite": 3}
        cursor.execute("""
            INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo = 1, parametros_json = excluded.parametros_json
        """, (servicio[0], regla_codigo, json.dumps(params)))
        print(f"Regla {regla_codigo} activada para el Servicio 2 con límite de {params['limite']}.")
        
        # 3. Desactivar/suspender la regla específicamente para POLETTI NATALIA
        # Comprobar si POLETTI NATALIA existe
        persona = cursor.execute("SELECT nombre FROM personal WHERE nombre = 'POLETTI NATALIA' AND servicio_id = 2").fetchone()
        if persona:
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json, activo = 1
            """, (persona[0], regla_codigo, json.dumps({"suspendida": True})))
            print(f"Regla {regla_codigo} suspendida individualmente para {persona[0]}.")
        else:
            print("Advertencia: No se encontró a POLETTI NATALIA en el Servicio 2.")
    else:
        print("Error: No se encontró el servicio con ID 2.")

    conn.commit()
    conn.close()
    print("Base de datos actualizada correctamente.")

if __name__ == '__main__':
    main()
