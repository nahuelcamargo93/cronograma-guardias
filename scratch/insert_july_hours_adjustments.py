import sqlite3
import json

def insert_adjustments():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()

    adjustments = [
        # Biscarra, Joaquín Martin
        ('Biscarra, Joaquín Martin', 'MIN_HORAS_MES_CALENDARIO', '{"min_horas": 145}'),
        ('Biscarra, Joaquín Martin', 'MAX_HORAS_MES_CALENDARIO', '{"max_horas": 170}'),
        
        # Villegas Oliva, Maria Belén
        ('Villegas Oliva, Maria Belén', 'MIN_HORAS_MES_CALENDARIO', '{"min_horas": 145}'),
        ('Villegas Oliva, Maria Belén', 'MAX_HORAS_MES_CALENDARIO', '{"max_horas": 170}'),
        
        # Matricadi, Wendy Ailen
        ('Matricadi, Wendy Ailen', 'MIN_HORAS_MES_CALENDARIO', '{"min_horas": 145}'),
        ('Matricadi, Wendy Ailen', 'MAX_HORAS_MES_CALENDARIO', '{"max_horas": 170}'),
        
        # Núñez, Florencia Natalia
        ('Núñez, Florencia Natalia', 'MIN_HORAS_MES_CALENDARIO', '{"min_horas": 145}'),
        ('Núñez, Florencia Natalia', 'MAX_HORAS_MES_CALENDARIO', '{"max_horas": 170}'),
        
        # Palermo, Agustín
        ('Palermo, Agustín', 'MIN_HORAS_MES_CALENDARIO', '{"min_horas": 145}'),
        ('Palermo, Agustín', 'MAX_HORAS_MES_CALENDARIO', '{"max_horas": 170}'),
    ]

    print("Insertando ajustes...")
    inserted_count = 0
    for name, rule, params in adjustments:
        # Check if already exists to avoid duplicates
        cursor.execute("""
            SELECT id FROM personal_reglas_ajustes
            WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = ? AND fecha_fin = ?
        """, (name, rule, '2026-07-01', '2026-07-31'))
        
        if cursor.fetchone():
            print(f"Ya existe un ajuste para {name} y regla {rule} en Julio 2026. Saltando.")
            continue
            
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, rule, '2026-07-01', '2026-07-31', 'SOBRESCRIBIR', params, 1, 3))
        inserted_count += 1

    conn.commit()
    print(f"Se insertaron {inserted_count} nuevos ajustes.")
    conn.close()

if __name__ == "__main__":
    insert_adjustments()
