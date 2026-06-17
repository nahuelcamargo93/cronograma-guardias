import sqlite3
import time
from database.connection import DB_PATH
import main

def test_diagnose():
    # 1. Conectarse a la BD con timeout largo
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Obtener supervisores dinámicamente
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 4 AND rol LIKE '%Supervisor%'")
    supervisores = [row[0] for row in cursor.fetchall()]
    
    print(f"[Test Setup] Insertando EXCLUIR_TURNOS el 2026-06-01 para todos los supervisores ({len(supervisores)})...")
    for name in supervisores:
        print(f"  - {name}")
    
    # Insertar regla conflictiva para todos
    # Excluimos todos los turnos de supervisor ese día
    param_json = '[{"turnos": ["00-06_Supervisor", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}]'
    for name in supervisores:
        cursor.execute(
            "INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo, servicio_id, parametros_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, 'EXCLUIR_TURNOS', '2026-06-01', '2026-06-01', 'SOBRESCRIBIR', 1, 4, param_json)
        )
    conn.commit()
    conn.close()
    
    try:
        # 2. Correr la optimización para el Servicio 4 con debug-hard
        print("\n[Test Run] Iniciando ejecución de optimización con --debug-hard...")
        res = main.ejecutar_optimizacion(
            servicio_id=4,
            fecha_inicio="2026-06-01",
            fecha_fin="2026-06-30",
            notas="Test de diagnostico debug-hard COM Exclusiones",
            modo_debug=False,
            max_time_in_seconds=30,
            diagnose=False,
            cronograma_base_id=0,
            modo_debug_hard=True
        )
        print(f"\n[Test Run] Resultado obtenido: {res}")
    finally:
        # Esperar un momento para liberar conexiones
        time.sleep(1.0)
        
        # 3. Restaurar base de datos
        print("\n[Test Teardown] Restaurando el estado original de la base de datos...")
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        # Eliminar las insertadas en la prueba
        for name in supervisores:
            cursor.execute(
                "DELETE FROM personal_reglas_ajustes WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = ?",
                (name, 'EXCLUIR_TURNOS', '2026-06-01')
            )
            
        conn.commit()
        conn.close()
        print("[Test Teardown] Base de datos restaurada.")

if __name__ == "__main__":
    test_diagnose()
