import sqlite3
import json
import sys, os
sys.path.append(os.getcwd())
from database.connection import get_connection

def migrar_nocturno_rotativo():
    servicio_id = 1

    with get_connection() as conn:
        # 1. Copiar reglas de Juarez al perfil "Nocturno"
        reglas_juarez = conn.execute("""
            SELECT codigo_regla, parametros_json
            FROM personal_reglas
            WHERE personal_nombre = 'Juarez, Eduardo' AND activo = 1
        """).fetchall()

        for cod, params in reglas_juarez:
            conn.execute("""
                INSERT OR REPLACE INTO roles_reglas (servicio_id, rol, codigo_regla, parametros_json, activo)
                VALUES (?, ?, ?, ?, 1)
            """, (servicio_id, 'Nocturno', cod, params))
            print(f"Copiada regla al rol Nocturno: {cod}")

        # 2. Limpiar reglas individuales de Juarez
        conn.execute("DELETE FROM personal_reglas WHERE personal_nombre = 'Juarez, Eduardo'")
        print("Limpiadas reglas individuales de Juarez (ahora hereda de rol Nocturno)")

        # 3. El rol "Rotativo" no tiene reglas propias (perfil vacío = sin restricciones extra)
        # No se inserta nada en roles_reglas para "Rotativo"
        print("Rol 'Rotativo' definido como perfil sin reglas adicionales (comportamiento base)")

        print("\n¡Migración completada!")

if __name__ == "__main__":
    migrar_nocturno_rotativo()
