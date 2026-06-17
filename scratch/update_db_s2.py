import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    c = conn.cursor()

    print('=== ANTES ===')
    turnos_antes = c.execute("SELECT id, nombre, hora_inicio, horas, servicio_id FROM turnos_config WHERE servicio_id = 2 AND nombre = 'N'").fetchall()
    print('Turnos N:', turnos_antes)
    demandas_antes = c.execute("SELECT id, puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max FROM demanda_config WHERE puesto_id = 9 AND hora_inicio = '00:00'").fetchall()
    print('Demandas 00-06:', demandas_antes)

    # Actualizar turnos_config
    c.execute("UPDATE turnos_config SET hora_inicio = '23:59' WHERE servicio_id = 2 AND nombre = 'N'")

    # Actualizar demanda_config
    c.execute("UPDATE demanda_config SET hora_inicio = '23:59', hora_fin = '05:59' WHERE puesto_id = 9 AND hora_inicio = '00:00' AND hora_fin = '06:00'")

    conn.commit()

    print('\n=== DESPUÉS ===')
    turnos_despues = c.execute("SELECT id, nombre, hora_inicio, horas, servicio_id FROM turnos_config WHERE servicio_id = 2 AND nombre = 'N'").fetchall()
    print('Turnos N:', turnos_despues)
    demandas_despues = c.execute("SELECT id, puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max FROM demanda_config WHERE puesto_id = 9 AND hora_inicio = '23:59'").fetchall()
    print('Demandas modificadas:', demandas_despues)

    conn.close()

if __name__ == '__main__':
    main()
