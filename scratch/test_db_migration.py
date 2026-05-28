import sqlite3
import json
import db as database
import rule_engine as _re

def test_migration():
    print("=== STARTING VERIFICATION ===")
    
    # 1. Clean existing adjustments for rule DESCANSO_ENTRE_TURNOS in service 3
    with database.get_connection() as conn:
        conn.execute("DELETE FROM servicios_reglas_ajustes WHERE servicio_id = 3 AND codigo_regla = 'DESCANSO_ENTRE_TURNOS';")
        conn.commit()
    print("Cleared any existing adjustments.")

    # 2. Query normal rules for service 3
    reglas_servicio = database.cargar_reglas_servicio(servicio_id=3)
    normal_descanso = reglas_servicio.get('DESCANSO_ENTRE_TURNOS')
    print(f"Normal DESCANSO_ENTRE_TURNOS for Service 3: {normal_descanso}")

    # 3. Insert temporal override for Service 3
    # From June 13 to June 15, reduce rest time to 24h
    override_params = {"por_turno": {"G": 24, "D": 24, "N": 24}}
    with database.get_connection() as conn:
        conn.execute("""
            INSERT INTO servicios_reglas_ajustes (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (3, 'DESCANSO_ENTRE_TURNOS', '2026-06-13', '2026-06-15', 'SOBRESCRIBIR', json.dumps(override_params), 1))
        conn.commit()
    print("Inserted temporal override for Service 3 (2026-06-13 to 2026-06-15).")

    # 4. Load adjustments
    ajustes_personal = database.cargar_ajustes_reglas_personal('2026-06-01', '2026-06-30')
    ajustes_servicio = database.cargar_ajustes_reglas_servicio('2026-06-01', '2026-06-30', 3)
    print(f"Loaded service adjustments: {ajustes_servicio}")
    
    ajustes_personal['__servicio__'] = ajustes_servicio

    # 5. Verify rule resolver behavior
    # Case A: Inside the override period (e.g. 2026-06-14)
    res_inside = _re.resolver_parametros_regla(
        'DESCANSO_ENTRE_TURNOS', 'Cualquier Medico', '2026-06-14',
        reglas_servicio, {}, ajustes_personal
    )
    print(f"Resolved parameters on 2026-06-14 (Inside): {res_inside}")
    assert res_inside == override_params, "Error: Should resolve to the override parameters."

    # Case B: Outside the override period (e.g. 2026-06-12)
    res_outside = _re.resolver_parametros_regla(
        'DESCANSO_ENTRE_TURNOS', 'Cualquier Medico', '2026-06-12',
        reglas_servicio, {}, ajustes_personal
    )
    print(f"Resolved parameters on 2026-06-12 (Outside): {res_outside}")
    assert res_outside == normal_descanso, f"Error: Should resolve to normal rules: {normal_descanso}"

    print("=== VERIFICATION SUCCESSFUL ===")

if __name__ == '__main__':
    test_migration()
