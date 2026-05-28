import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def apply_fixes():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=== APPLYING DATABASE FIXES TO cronograma_inteligente.db ===")
    
    # 1. Update EXCLUIR_TURNOS for GUERRIDO Noelia to Category A exclusions
    new_exclusions = '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions,))
    print(f"1. Updated EXCLUIR_TURNOS for GUERRIDO Noelia: {cursor.rowcount} row(s) updated.")

    # 2. Insert MIN_HORAS_MES_CALENDARIO and MAX_HORAS_MES_CALENDARIO for June 2026 for GUERRIDO Noelia
    cursor.execute("""
        SELECT 1 FROM personal_reglas_ajustes 
        WHERE personal_nombre = 'GUERRIDO Noelia' 
          AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO' 
          AND fecha_inicio = '2026-06-01'
    """)
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES 
            ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
            ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
        """)
        print(f"2. Inserted MIN/MAX hours adjustments for GUERRIDO Noelia for June 2026.")
    else:
        print(f"2. MIN/MAX hours adjustments for GUERRIDO Noelia already exist.")

    # 3. Update FINDES_COMPLETOS_Y_MEDIOS for SUAREZ Carolina to SUSPENDER
    cursor.execute("""
        UPDATE personal_reglas_ajustes
        SET accion = 'SUSPENDER'
        WHERE personal_nombre = 'SUAREZ Carolina' AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS'
    """)
    print(f"3. Suspended FINDES_COMPLETOS_Y_MEDIOS for SUAREZ Carolina: {cursor.rowcount} row(s) updated.")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] All fixes successfully applied to the database!")

if __name__ == "__main__":
    apply_fixes()
