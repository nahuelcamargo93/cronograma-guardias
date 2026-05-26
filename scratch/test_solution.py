import sys
import os
sys.path.append(os.path.abspath("."))
import sqlite3
import debug_imposibilidad
import main

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Run the update queries
try:
    # 1. Disable PESO_EQUIDAD_FINDES_MENSUAL
    cursor.execute("""
    UPDATE servicios_reglas 
    SET activo = 0 
    WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL';
    """)
    
    # 2. Insert FINDES_COMPLETOS_Y_MEDIOS for service 4
    cursor.execute("""
    INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
    VALUES (
        4, 
        'FINDES_COMPLETOS_Y_MEDIOS', 
        '{"por_disponibilidad": {"4": {"completos": 2, "medios": 0}, "5": {"completos": 2, "medios": 1}, "3": {"completos": 1, "medios": 1}, "2": {"completos": 1, "medios": 0}, "1": {"completos": 0, "medios": 1}, "0": {"completos": 0, "medios": 0}}}', 
        1
    );
    """)
    
    # 3. Suspend FINDES_COMPLETOS_Y_MEDIOS for Category A staff
    cat_a_names = ["FERNANDEZ Celeste Ivana", "FERNANDEZ Juan Emir", "FLORES Enzo", "KOPRIVSEK Francisco", "ESCUDERO Gabriela", "FERNANDEZ Claudia Elizabeth", "OLGUIN ALDECO Jennifer Sofia"]
    for name in cat_a_names:
        cursor.execute("""
        INSERT OR REPLACE INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
        VALUES (?, 'FINDES_COMPLETOS_Y_MEDIOS', '{"suspendida": true}', 1);
        """, (name,))
        
    conn.commit()
    print("Database configured for testing.")
except Exception as e:
    print("Error:", e)
    conn.rollback()

conn.close()

# Now run a test feasibility check for service 4
print("\n--- Running Imposibilidad Check for Service 4 with Category A suspended ---")
debug_imposibilidad.reportar_imposibilidad(4, "2026-06-01", "2026-06-30")

# Revert database changes so we don't pollute user's DB yet
conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()
cursor.execute("""
UPDATE servicios_reglas 
SET activo = 1 
WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL';
""")
cursor.execute("""
DELETE FROM servicios_reglas 
WHERE servicio_id = 4 AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS';
""")
for name in cat_a_names:
    cursor.execute("""
    DELETE FROM personal_reglas
    WHERE personal_nombre = ? AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS';
    """, (name,))
conn.commit()
conn.close()
print("\nReverted test database changes.")
