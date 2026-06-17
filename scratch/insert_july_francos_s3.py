import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()

    francos = [
        ("Arias, Guillermina", "2026-07-08", "2026-07-12"),
        ("Kolarik, Jorge Luis", "2026-07-08", "2026-07-12"),
        ("Silva, Martín Enrique", "2026-07-08", "2026-07-12"),
        ("Mora, Sergio Enrique", "2026-07-08", "2026-07-12"),
        ("Nesteruk, María Silvia", "2026-07-08", "2026-07-12"),
        ("Pregot, Analia Mariana", "2026-07-08", "2026-07-12"),
        ("Quiroga Sassu, Maria Macarena", "2026-07-08", "2026-07-12"),
        ("Zeballos, Valeria Alejandra", "2026-07-08", "2026-07-12"),
        ("Palermo, Agustín", "2026-07-08", "2026-07-12"),
        ("Matricadi, Wendy Ailen", "2026-07-08", "2026-07-12"),
        ("Villegas Oliva, Maria Belén", "2026-07-08", "2026-07-12"),
    ]

    print("--- REGISTRANDO FRANCOS FORZADOS (SERVICIO ID 3) ---")
    inserted_count = 0
    for nombre, inicio, fin in francos:
        # Eliminar registros previos idénticos/solapados para evitar duplicidad
        cursor.execute("""
            DELETE FROM personal_reglas_ajustes
            WHERE personal_nombre = ? AND codigo_regla = 'FRANCO_FORZADO' AND fecha_inicio = ? AND fecha_fin = ? AND servicio_id = 3
        """, (nombre, inicio, fin))
        
        # Insertar nuevo registro
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (
                personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id
            ) VALUES (?, 'FRANCO_FORZADO', ?, ?, 'SOBRESCRIBIR', '{}', 1, 3)
        """, (nombre, inicio, fin))
        
        print(f"Registrado franco forzado para {nombre} desde {inicio} hasta {fin} (ID: {cursor.lastrowid})")
        inserted_count += 1

    conn.commit()
    print(f"\nSe han insertado/actualizado {inserted_count} francos forzados exitosamente.")
    conn.close()

if __name__ == "__main__":
    main()
