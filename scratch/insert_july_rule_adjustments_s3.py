import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()

    servicio_id = 3
    codigo_regla = "DESCANSO_ENTRE_TURNOS"
    fecha_inicio = "2026-07-08"
    fecha_fin = "2026-07-12"
    accion = "SOBRESCRIBIR"
    parametros_json = '{"por_turno": {"G": 24, "D": 12, "N": 24}}'

    print("--- REGISTRANDO AJUSTE DE REGLA EN SERVICIO 3 ---")
    
    # Eliminar registros previos con las mismas características para evitar duplicidad
    cursor.execute("""
        DELETE FROM servicios_reglas_ajustes
        WHERE servicio_id = ? AND codigo_regla = ? AND fecha_inicio = ? AND fecha_fin = ? AND activo = 1
    """, (servicio_id, codigo_regla, fecha_inicio, fecha_fin))

    # Insertar el nuevo ajuste
    cursor.execute("""
        INSERT INTO servicios_reglas_ajustes (
            servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json))

    conn.commit()
    print(f"Registrado ajuste para {codigo_regla} desde {fecha_inicio} hasta {fecha_fin} (ID: {cursor.lastrowid})")
    conn.close()

if __name__ == "__main__":
    main()
