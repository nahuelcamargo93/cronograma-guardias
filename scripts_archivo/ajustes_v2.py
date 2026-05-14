import sqlite3

def aplicar():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # Limpiar todos los ajustes actuales
    cursor.execute("DELETE FROM turnos_ajustes")

    # Obtener IDs de turnos
    turnos = {n: i for i, n in cursor.execute("SELECT id, nombre FROM turnos_config WHERE servicio_id = 1").fetchall()}
    print("Turnos encontrados:", turnos)

    id_m_uti    = turnos.get("Ma\xf1ana_UTI")
    id_t_uti    = turnos.get("Tarde_UTI")
    id_m_esp    = turnos.get("Ma\xf1ana_especial")
    id_t_esp    = turnos.get("Tarde_especial")

    if not id_m_uti:
        print("ERROR: No se encontro Manana_UTI en turnos_config")
        conn.close()
        return

    ajustes = [
        # Semana 1 (01/06 - 07/06): -1 manana, -1 tarde
        ('2026-06-01', '2026-06-07', id_m_uti, 4, None),
        ('2026-06-01', '2026-06-07', id_t_uti, 2, None),

        # Semana 2a (08/06 - 10/06): Mañana_UTI = 4
        ('2026-06-08', '2026-06-10', id_m_uti, 4, None),
        ('2026-06-08', '2026-06-10', id_t_uti, 2, None),

        # Semana 2b (11/06 - 14/06): Mañana_UTI vuelve a 5
        ('2026-06-11', '2026-06-14', id_m_uti, 5, None),
        ('2026-06-11', '2026-06-14', id_t_uti, 2, None),

        # Semana 3 (15/06 - 21/06): Mañana_UTI = 3, saca especiales
        ('2026-06-15', '2026-06-21', id_m_uti, 3, None),
        ('2026-06-15', '2026-06-21', id_t_uti, 2, None),
        ('2026-06-15', '2026-06-21', id_m_esp, 0, None),
        ('2026-06-15', '2026-06-21', id_t_esp, 0, None),

        # Semana 4 (22/06 - 28/06): -1 manana, -1 tarde
        ('2026-06-22', '2026-06-28', id_m_uti, 4, None),
        ('2026-06-22', '2026-06-28', id_t_uti, 2, None),
    ]

    # Filtrar ajustes si el ID no existe
    ajustes = [(fi, ff, t_id, vac, d_ov) for fi, ff, t_id, vac, d_ov in ajustes if t_id is not None]

    for fi, ff, t_id, vac, d_ov in ajustes:
        cursor.execute("""
            INSERT INTO turnos_ajustes (turno_config_id, fecha_inicio, fecha_fin, vacantes, dias_semana)
            VALUES (?, ?, ?, ?, ?)
        """, (t_id, fi, ff, vac, d_ov))

    conn.commit()
    print(f"OK: {len(ajustes)} ajustes aplicados.")

    # Verificar
    print("\n--- AJUSTES ACTUALES ---")
    rows = cursor.execute("""
        SELECT ta.fecha_inicio, ta.fecha_fin, tc.nombre, ta.vacantes
        FROM turnos_ajustes ta
        JOIN turnos_config tc ON ta.turno_config_id = tc.id
        ORDER BY ta.fecha_inicio, tc.nombre
    """).fetchall()
    for r in rows:
        print(f"  {r[0]} -> {r[1]} | {r[2]:<18} | {r[3]}")

    conn.close()

if __name__ == "__main__":
    aplicar()
