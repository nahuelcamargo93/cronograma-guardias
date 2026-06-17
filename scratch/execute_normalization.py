import sqlite3
import json
import os

DB_PATH = "cronograma_inteligente.db"

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} no existe.")
        return

    # Definir el mapeo completo de nombres
    mapping = {
        # Servicio 1 (Kinesiología)
        "Lic. Camargo N.": "Camargo, Nahuel",
        "Lic. Garcia": "Garcia, Luciano",
        "Lic. Giaccoppo": "Giacoppo, Veronica",
        "Lic. Sosa": "Sosa, Nicolas",
        "Lic. Juarez": "Juarez, Eduardo",
        "Lic. Guardia": "Guardia, Gabriel",
        "Lic. Toledo": "Toledo, Andrea",
        "Lic. Moyano": "Moyano, Fernando",
        "Lic. Marino": "Marino, Emiliano",
        "Lic. Mesa": "Mesa, Bruno",
        "Lic. Syriani": "Syriani, Danae",
        "Lic. Leonforte": "Leonforte, Franco",
        "Lic. Guzman": "Guzman, Ariel",
        "Lic. Flores": "Flores, Franco",
        "Lic. Franco": "Franco, Leandro",
        "Lic. Coniglio": "Coniglio, Melisa",
        "Lic. Welch": "Welch, Lucas",
        "Lic. Espinosa": "Espinosa, Elizabeth",
        "Lic. Vander": "Vander, Nicolas",
        "Lic. Vivas": "Vivas, Eric",
        
        # Servicio 3 (Área Médica UTI)
        "Aguilera Graciela": "Aguilera, Graciela",
        "Arias Guillermina": "Arias, Guillermina",
        "Baracat Denisse": "Baracat, Denisse",
        "Barloa Matías Damián": "Barloa, Matías Damián",
        "Barloa Mat\xedas Dami\xe1n": "Barloa, Matías Damián", # fallback por si acaso
        "Diaz Villafañe Morales Abigail": "Diaz Villafañe Morales, Abigail",
        "Diaz Villafa\xf1e Morales Abigail": "Diaz Villafañe Morales, Abigail", # fallback
        "Garcia Rodriguez, Maria Eugenia.": "Garcia Rodriguez, Maria Eugenia",
        "Godoy Maria": "Godoy, Maria",
        "Kolarik Jorge Luis": "Kolarik, Jorge Luis",
        "Silva, Martín Enrique": "Silva, Martín Enrique",
        "Silva, Mart\xedn Enrique": "Silva, Martín Enrique", # fallback
        "Mora, Sergio Enrique": "Mora, Sergio Enrique",
        "Motta, Mayra Belen": "Motta, Mayra Belen",
        "Moya, Pedro": "Moya, Pedro",
        "Murillo, Santiago": "Murillo, Santiago",
        "Navarro Suarez Gabriela Belén": "Navarro Suarez, Gabriela Belén",
        "Navarro Suarez Gabriela Bel\xe9n": "Navarro Suarez, Gabriela Belén", # fallback
        "Nesteruk María Silvia": "Nesteruk, María Silvia",
        "Nesteruk Mar\xeda Silvia": "Nesteruk, María Silvia", # fallback
        "Noriega Claudio Martín": "Noriega, Claudio Martín",
        "Noriega Claudio Mart\xedn": "Noriega, Claudio Martín", # fallback
        "Pregot Analia Mariana": "Pregot, Analia Mariana",
        "Quintero Anabela Belen": "Quintero, Anabela Belen",
        "Quiroga Sassu Maria Macarena": "Quiroga Sassu, Maria Macarena",
        "Sánchez Reinoso Ana Belén": "Sánchez Reinoso, Ana Belén",
        "S\xe1nchez Reinoso Ana Bel\xe9n": "Sánchez Reinoso, Ana Belén", # fallback
        "Zeballos Valeria Alejandra": "Zeballos, Valeria Alejandra",
        "Arce Carolina": "Arce, Carolina",
        "Pacheco Celeste": "Pacheco, Celeste",
        "Biscarra Joaquín Martin": "Biscarra, Joaquín Martin",
        "Biscarra Joaqu\xedn Martin": "Biscarra, Joaquín Martin", # fallback
        "Villegas Oliva Maria Belén": "Villegas Oliva, Maria Belén",
        "Villegas Oliva Maria Bel\xe9n": "Villegas Oliva, Maria Belén", # fallback
        "Matricadi Wendy Ailen": "Matricadi, Wendy Ailen",
        "Núñez Florencia Natalia": "Núñez, Florencia Natalia",
        "N\xfa\xf1ez Florencia Natalia": "Núñez, Florencia Natalia", # fallback
        "Palermo Agustín": "Palermo, Agustín",
        "Palermo Agust\xedn": "Palermo, Agustín", # fallback
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Habilitar claves foráneas para estar seguros, aunque lo manejaremos explícitamente
        cursor.execute("PRAGMA foreign_keys = OFF") # Lo apagamos para evitar que bloquee actualizaciones parciales intermedia de PK
        
        # 1. Corregir rol de Moya, Pedro en la tabla personal
        cursor.execute("UPDATE personal SET rol = 'Planta' WHERE nombre = 'Moya, Pedro'")
        print("Corregido el rol de Moya, Pedro a 'Planta' en tabla personal.")

        # Tablas que referencian al personal por su nombre
        # (nombre_tabla, nombre_columna_referencia)
        referencias = [
            ("guardias", "nombre"),
            ("personal_reglas_ajustes", "personal_nombre"),
            ("flr_asignados", "nombre"),
            ("personal_puestos", "personal_nombre"),
            ("semanas_categorias", "nombre"),
            ("licencias", "nombre"),
            ("personal_reglas", "personal_nombre"),
        ]

        total_updates = 0

        # Primero actualizamos las referencias externas
        for old_name, new_name in mapping.items():
            # Verificar si existe el viejo nombre en la tabla 'personal'
            cursor.execute("SELECT count(*) FROM personal WHERE nombre = ?", (old_name,))
            if cursor.fetchone()[0] == 0:
                continue

            print(f"Migrando: '{old_name}' -> '{new_name}'")
            
            # Actualizar en las tablas satélites primero
            for table, col in referencias:
                cursor.execute(f"UPDATE {table} SET {col} = ? WHERE {col} = ?", (new_name, old_name))
                row_count = cursor.rowcount
                if row_count > 0:
                    print(f"  - Tabla '{table}': actualizados {row_count} registros.")
                    total_updates += row_count

            # Finalmente actualizar en la tabla principal (personal)
            # Para evitar conflictos de clave primaria si el nuevo nombre ya existe (por ejemplo, si corremos esto de nuevo),
            # usamos INSERT OR IGNORE o validamos. Como es una migración limpia, un simple UPDATE es lo correcto.
            cursor.execute("UPDATE personal SET nombre = ? WHERE nombre = ?", (new_name, old_name))
            if cursor.rowcount > 0:
                print(f"  - Tabla 'personal': nombre actualizado en la clave primaria.")
                total_updates += 1

        # 2. Actualizar JSON en servicios_reglas (Regla ID 62 del Servicio 3)
        # JSON original: {"nombres": ["Baracat Denisse", "Moya, Pedro", "Mora, Sergio Enrique"]}
        cursor.execute("SELECT id, parametros_json FROM servicios_reglas WHERE id = 62")
        row = cursor.fetchone()
        if row:
            r_id, p_json_str = row
            if p_json_str:
                p_json = json.loads(p_json_str)
                if "nombres" in p_json:
                    viejos_nombres = p_json["nombres"]
                    nuevos_nombres = []
                    for vn in viejos_nombres:
                        # Buscar en mapeo
                        nn = mapping.get(vn, vn)
                        nuevos_nombres.append(nn)
                    p_json["nombres"] = nuevos_nombres
                    nuevo_json_str = json.dumps(p_json, ensure_ascii=False)
                    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?", (nuevo_json_str, r_id))
                    print(f"Actualizado JSON de servicios_reglas ID {r_id}: {nuevo_json_str}")
                    total_updates += 1

        # Commit de todos los cambios
        conn.commit()
        print("\nTransacción confirmada con éxito.")
        print(f"Total de registros actualizados en todas las tablas: {total_updates}")

    except Exception as e:
        conn.rollback()
        print(f"\nError durante la migración: {e}")
        print("Se ha realizado un ROLLBACK. Ningún cambio fue guardado.")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
