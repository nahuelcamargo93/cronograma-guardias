import os
import sys
import sqlite3

def check():
    db_path = 'cronograma_inteligente.db'
    crono_id = 348 # Último cronograma generado según los logs
    
    print(f"Verificando asignaciones de turnos especiales para el cronograma ID {crono_id}...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Obtener todas las asignaciones a turnos especiales
        cursor.execute("""
            SELECT fecha, nombre, turno 
            FROM guardias 
            WHERE cronograma_id = ? AND (turno LIKE '%especial%' OR turno LIKE '%Especial%')
            ORDER BY fecha, turno, nombre
        """, (crono_id,))
        
        guardias_especiales = cursor.fetchall()
        
        print(f"\nSe encontraron {len(guardias_especiales)} guardias asignadas en turnos especiales:")
        print(f"{'Fecha':<12} | {'Nombre':<20} | {'Turno':<20}")
        print("-" * 60)
        for fecha, nombre, turno in guardias_especiales:
            print(f"{fecha:<12} | {nombre:<20} | {turno:<20}")

        # 2. Obtener todas las asignaciones fijas configuradas para ver si coinciden
        print("\n--- ASIGNACIONES FIJAS DE TURNOS ESPECIALES EN LA BASE DE DATOS ---")
        cursor.execute("""
            SELECT personal_nombre, parametros_json 
            FROM personal_reglas 
            WHERE codigo_regla = 'ASIGNACION_FIJA' AND activo = 1
        """)
        reglas_fijas = cursor.fetchall()
        for nombre, params_str in reglas_fijas:
            import json
            try:
                params = json.loads(params_str)
                for p in params:
                    t = p.get('Turno')
                    if t and ('especial' in t.lower() or 'Especial' in t):
                        print(f"Empleado: {nombre} | Regla: {p}")
            except Exception as e:
                print(f"Error parseando para {nombre}: {e}")

if __name__ == '__main__':
    check()
