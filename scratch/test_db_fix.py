import sqlite3
import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_cronograma_inteligente.db")
ORIG_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

# Copy the database
shutil.copyfile(ORIG_DB, TEMP_DB)

# Override DB_PATH in database.connection
import database.connection
database.connection.DB_PATH = TEMP_DB

from debug_imposibilidad import reportar_imposibilidad
from data import SERVICIO_ID, FECHA_INICIO, FECHA_FIN

def apply_test_fixes():
    conn = sqlite3.connect(TEMP_DB)
    cursor = conn.cursor()
    
    # 1. Update EXCLUIR_TURNOS for GUERRIDO Noelia to Category A exclusions
    new_exclusions = '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions,))
    print(f"Updated EXCLUIR_TURNOS for GUERRIDO Noelia: {cursor.rowcount} row(s) updated.")

    # 2. Insert MIN_HORAS_MES_CALENDARIO and MAX_HORAS_MES_CALENDARIO for June 2026
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
        VALUES 
        ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
        ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
    """)
    print(f"Inserted hour adjustments for GUERRIDO Noelia: {cursor.rowcount} row(s) inserted.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        print("Applying test fixes to temporary database...")
        apply_test_fixes()
        
        print("\nRunning diagnostic on temporary database...")
        reportar_imposibilidad(SERVICIO_ID, FECHA_INICIO, FECHA_FIN)
        
    finally:
        # Clean up temporary database
        if os.path.exists(TEMP_DB):
            os.remove(TEMP_DB)
            print("\nTemporary database cleaned up.")
