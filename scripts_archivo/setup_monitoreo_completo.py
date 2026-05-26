import sqlite3

def run_setup():
    sql = """
    BEGIN TRANSACTION;

    -- 1. Limpiar configuracion y personal previo del servicio 4
    DELETE FROM turnos_config WHERE servicio_id = 4;
    DELETE FROM puestos WHERE servicio_id = 4;
    DELETE FROM personal_puestos WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 4);
    DELETE FROM personal_reglas WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 4);
    DELETE FROM personal WHERE servicio_id = 4;

    -- 2. Insertar los dos nuevos puestos para el servicio 4
    INSERT INTO puestos (servicio_id, nombre) VALUES (4, 'Supervisor');
    INSERT INTO puestos (servicio_id, nombre) VALUES (4, 'Monitorista');

    -- 3. Insertar la configuracion de los 8 turnos (4 para Supervisor, 4 para Monitorista)
    INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, orden, dias_semana, puesto_id, activo) VALUES
    (4, '00-06_Supervisor', '00:00', 6, 1, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4), 1),
    (4, '06-12_Supervisor', '06:00', 6, 2, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4), 1),
    (4, '12-18_Supervisor', '12:00', 6, 3, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4), 1),
    (4, '18-24_Supervisor', '18:00', 6, 4, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4), 1),
    (4, '00-06_Monitorista', '00:00', 6, 5, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4), 1),
    (4, '06-12_Monitorista', '06:00', 6, 6, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4), 1),
    (4, '12-18_Monitorista', '12:00', 6, 7, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4), 1),
    (4, '18-24_Monitorista', '18:00', 6, 8, '0,1,2,3,4,5,6', (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4), 1);

    -- 4. Insertar al personal en la tabla 'personal' (roles vacios se configuran como 'Monitorista')
    INSERT INTO personal (nombre, categoria, rol, servicio_id, es_madre, es_padre) VALUES
    ('FERNANDEZ Celeste Ivana', 'A', 'Monitorista', 4, 0, 0),
    ('FERNANDEZ Claudia Elizabeth', 'A', 'Supervisor Suplente', 4, 0, 0),
    ('FERNANDEZ Juan Emir', 'A', 'Monitorista', 4, 0, 0),
    ('FLORES Enzo', 'A', 'Monitorista', 4, 0, 0),
    ('KOPRIVSEK Francisco', 'A', 'Monitorista', 4, 0, 0),
    ('OLGUIN ALDECO Jennifer Sofia', 'A', 'Supervisor Titular', 4, 0, 0),
    ('ESCUDERO Gabriela', 'A', 'Monitorista', 4, 0, 0),
    ('ALCARAZ Xavier', 'B', 'Monitorista', 4, 0, 0),
    ('OJEDA Miriam', 'B', 'Monitorista', 4, 0, 0),
    ('RUOCCO MUÑOZ Luis Alfredo', 'B', 'Supervisor Suplente', 4, 0, 0),
    ('STEIMBRECHER Yolanda', 'B', 'Monitorista', 4, 0, 0),
    ('LEDESMA PAZ Micaela', 'B', 'Monitorista', 4, 0, 0),
    ('MANSILLA Diego', 'B', 'Monitorista', 4, 0, 0),
    ('MESSINA Eduardo', 'B', 'Monitorista', 4, 0, 0),
    ('RODRIGUEZ Maximiliano', 'B', 'Monitorista', 4, 0, 0),
    ('SANCIO Paola', 'B', 'Supervisor Titular', 4, 0, 0),
    ('BARROSO Alan', 'C', 'Monitorista', 4, 0, 0),
    ('SUÑER Mara Tatiana', 'C', 'Monitorista', 4, 0, 0),
    ('FLORES Jose Nicolas', 'C', 'Monitorista', 4, 0, 0),
    ('BRIZUELA Irma', 'C', 'Supervisor Suplente', 4, 0, 0),
    ('GUERRERO Cesar', 'C', 'Monitorista', 4, 0, 0),
    ('MOCDESE Marcelo Leonel', 'C', 'Monitorista', 4, 0, 0),
    ('TORRES Yesica', 'C', 'Supervisor Titular', 4, 0, 0),
    ('VERGARA Nazareno', 'C', 'Monitorista', 4, 0, 0),
    ('VILLEGAS Gaston', 'C', 'Monitorista', 4, 0, 0),
    ('FUNEZ Valeria Vanesa', 'D', 'Monitorista', 4, 0, 0),
    ('GUERRIDO Noelia', 'D', 'Supervisor Suplente', 4, 0, 0),
    ('MIRANDA Luis', 'D', 'Monitorista', 4, 0, 0),
    ('MUÑOZ Maria Carolina', 'D', 'Monitorista', 4, 0, 0),
    ('QUINTANA Felipe Gabriel', 'D', 'Monitorista', 4, 0, 0),
    ('SUAREZ Carolina', 'D', 'Supervisor Titular', 4, 0, 0),
    ('VELEZ Facundo', 'D', 'Monitorista', 4, 0, 0),
    ('VERGARA Mariano', 'D', 'Monitorista', 4, 0, 0);

    -- 5. Mapear habilitacion de puestos en 'personal_puestos'
    -- Supervisor Titular -> Supervisor
    INSERT INTO personal_puestos (personal_nombre, puesto_id)
    SELECT nombre, (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4)
    FROM personal WHERE servicio_id = 4 AND rol = 'Supervisor Titular';

    -- Monitorista -> Monitorista
    INSERT INTO personal_puestos (personal_nombre, puesto_id)
    SELECT nombre, (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4)
    FROM personal WHERE servicio_id = 4 AND rol = 'Monitorista';

    -- Supervisor Suplente -> Supervisor Y Monitorista
    INSERT INTO personal_puestos (personal_nombre, puesto_id)
    SELECT nombre, (SELECT id FROM puestos WHERE nombre = 'Supervisor' AND servicio_id = 4)
    FROM personal WHERE servicio_id = 4 AND rol = 'Supervisor Suplente';

    INSERT INTO personal_puestos (personal_nombre, puesto_id)
    SELECT nombre, (SELECT id FROM puestos WHERE nombre = 'Monitorista' AND servicio_id = 4)
    FROM personal WHERE servicio_id = 4 AND rol = 'Supervisor Suplente';

    -- 6. Aplicar la regla EXCLUIR_TURNOS (regla ID 4) segun Categoria (A, B, C, D)
    -- Categoria A (solo trabaja 00-06)
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    SELECT nombre, 4, '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    FROM personal WHERE servicio_id = 4 AND categoria = 'A';

    -- Categoria B (solo trabaja 06-12)
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    SELECT nombre, 4, '{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    FROM personal WHERE servicio_id = 4 AND categoria = 'B';

    -- Categoria C (solo trabaja 12-18)
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    SELECT nombre, 4, '{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "18-24_Supervisor"]}'
    FROM personal WHERE servicio_id = 4 AND categoria = 'C';

    -- Categoria D (solo trabaja 18-24)
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    SELECT nombre, 4, '{"turnos": ["00-06_Monitorista", "06-12_Monitorista", "12-18_Monitorista", "00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor"]}'
    FROM personal WHERE servicio_id = 4 AND categoria = 'D';

    COMMIT;
    """
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    try:
        conn.executescript(sql)
        print("[SUCCESS] Setup executed successfully inside the database!")
    except Exception as e:
        print(f"[ERROR] Error executing setup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_setup()
