import sqlite3

def run_simplified_fixes():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # 1. Limpieza total
    cursor.execute("DELETE FROM turnos_ajustes")
    cursor.execute("DELETE FROM personal_reglas_ajustes")

    # IDs
    M_UTI = 5; T_UTI = 8; D_UTI = 6
    M_UCO = 7; T_UCO = 4; D_UCO = 2

    # 2. Ajustes de Turnos (1 de Junio al 5 de Julio - TODO EL MES)
    inicio = "2026-06-01"
    fin = "2026-07-05"
    dias = "0,1,2,3,4" # Lunes a Viernes

    # Plan de eficiencia: Usar 12h para reducir personal
    # 1 Dia_UTI (12h) + 3 Mañana_UTI (6h) + 1 Tarde_UTI (6h) = Total 4 Mañana / 2 Tarde
    # 1 Dia_UCO (12h) en vez de Mañana+Tarde UCO
    ajustes = [
        (D_UTI, 1), (M_UTI, 3), (T_UTI, 1),
        (D_UCO, 1), (M_UCO, 0), (T_UCO, 0)
    ]
    
    for tid, vac in ajustes:
        cursor.execute(f"""
            INSERT INTO turnos_ajustes (turno_config_id, fecha_inicio, fecha_fin, vacantes, dias_semana) 
            VALUES (?, ?, ?, ?, ?)
        """, (tid, inicio, fin, vac, dias))

    # 3. Ajustes de Personal (Especialidades suspendidas todo el mes)
    for p in ['Lic. Camargo N.', 'Lic. Giaccoppo']:
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion) 
            VALUES (?, 'ASIGNACION_FIJA', ?, ?, 'SUSPENDER')
        """, (p, inicio, fin))
    
    # Coniglio solo la primera semana (como estaba en el plan original)
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion) 
        VALUES ('Lic. Coniglio', 'ASIGNACION_FIJA', '2026-06-01', '2026-06-07', 'SUSPENDER')
    """)

    conn.commit()
    conn.close()
    print("Ajustes simplificados cargados correctamente.")

if __name__ == "__main__":
    run_simplified_fixes()
