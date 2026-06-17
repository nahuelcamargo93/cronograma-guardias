import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

updates = {
    "Moyano, Fernando": [
        {"turnos": ["Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Noche", "Tarde_UTI"], "dias": [0, 1, 2, 3, 4, 5, 6]},
        {"turnos": ["Dia_UTI", "Dia_UCO", "Dia_especial"], "dias": [0, 1, 2, 3, 4]}
    ],
    "Franco, Leandro": [
        {"turnos": ["Tarde_UTI", "Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Noche"], "dias": [0, 1, 2, 3, 4, 5, 6]},
        {"turnos": ["Dia_UTI", "Dia_UCO", "Dia_especial"], "dias": [0, 1, 2, 3, 4]}
    ],
    "Garcia, Luciano": [
        {"turnos": ["Tarde_UTI", "Noche", "Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Mañana_especial", "Tarde_especial"], "dias": [0, 1, 2, 3, 4, 5, 6]},
        {"turnos": ["Dia_UTI", "Dia_UCO", "Dia_especial"], "dias": [0, 1, 2, 3, 4]}
    ],
    "Toledo, Andrea": [
        {"turnos": ["Mañana_UTI", "Tarde_UTI", "Tarde_UCO", "Noche", "Dia_UTI"], "dias": [0, 1, 2, 3, 4, 5, 6]},
        {"turnos": ["Dia_UCO", "Dia_UTI"], "dias": [0, 1, 2, 3, 4]}
    ]
}

print("=== ACTUALIZANDO REGLAS DE EXCLUSIÓN EN BD ===")
for nombre, params in updates.items():
    params_str = json.dumps(params, ensure_ascii=False)
    # Verificar si ya existe la regla para esa persona
    cursor.execute("""
        SELECT COUNT(*) FROM personal_reglas 
        WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (nombre,))
    exists = cursor.fetchone()[0]
    
    if exists:
        cursor.execute("""
            UPDATE personal_reglas 
            SET parametros_json = ?, activo = 1
            WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'
        """, (params_str, nombre))
        print(f"[UPDATE] {nombre}: Regla de exclusión actualizada.")
    else:
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
            VALUES (?, 'EXCLUIR_TURNOS', ?, 1)
        """, (nombre, params_str))
        print(f"[INSERT] {nombre}: Nueva regla de exclusión creada.")

conn.commit()
conn.close()
print("=== ACTUALIZACIÓN COMPLETADA ===")
