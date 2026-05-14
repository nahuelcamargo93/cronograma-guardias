import sqlite3

def aplicar_ajustes_criticos():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # 1. Limpiar ajustes actuales
    cursor.execute("DELETE FROM turnos_ajustes")
    
    # 2. Obtener IDs de los turnos (Mañana_UTI=5, Tarde_UTI=8 usualmente, pero buscaremos)
    cursor.execute("SELECT id, nombre FROM turnos_config WHERE servicio_id = 1")
    turnos = {nombre: id for id, nombre in cursor.fetchall()}
    
    id_m_uti = turnos.get("Mañana_UTI")
    id_t_uti = turnos.get("Tarde_UTI")
    
    if not id_m_uti or not id_t_uti:
        print("Error: No se encontraron los turnos Mañana_UTI o Tarde_UTI")
        return

    # 3. Definir ajustes (fi, ff, turno_id, vacantes)
    ajustes = [
        # Semana 1 (01/06)
        ('2026-06-01', '2026-06-07', id_m_uti, 4),
        ('2026-06-01', '2026-06-07', id_t_uti, 2),
        # Semana 2 (08/06)
        ('2026-06-08', '2026-06-14', id_m_uti, 4),
        ('2026-06-08', '2026-06-14', id_t_uti, 2),
        # Semana 3 (15/06) - Mas critica: bajamos Mañana a 3
        ('2026-06-15', '2026-06-21', id_m_uti, 3),
        ('2026-06-15', '2026-06-21', id_t_uti, 2),
        # Semana 4 (22/06) - Empieza a normalizar
        ('2026-06-22', '2026-06-28', id_m_uti, 4),
        ('2026-06-22', '2026-06-28', id_t_uti, 2),
    ]

    for fi, ff, t_id, vac in ajustes:
        cursor.execute("""
            INSERT INTO turnos_ajustes (turno_config_id, fecha_inicio, fecha_fin, vacantes)
            VALUES (?, ?, ?, ?)
        """, (t_id, fi, ff, vac))

    conn.commit()
    print(f"OK: Se aplicaron {len(ajustes)} ajustes de vacantes para las semanas criticas.")
    conn.close()

if __name__ == "__main__":
    aplicar_ajustes_criticos()
