import sqlite3
import subprocess
import shutil
import os
import pandas as pd

def main():
    db_file = "cronograma_inteligente.db"
    backup_file = "cronograma_inteligente.db.bak"
    
    # 1. Hacer backup de la BD
    if os.path.exists(db_file):
        shutil.copyfile(db_file, backup_file)
        print("Backup creado con éxito.")
    else:
        print("No se encontró la base de datos.")
        return

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 2. Asegurarse de que turnos_config para 00-06_Monitorista esté en '0,1,2,3,4,5,6'
        cursor.execute("""
            UPDATE turnos_config 
            SET dias_semana = '0,1,2,3,4,5,6' 
            WHERE puesto_id = 32 AND nombre = '00-06_Monitorista'
        """)
        
        # 3. Insertar la demanda específica de 0 personas en sábados y domingos (dias_semana = '5,6')
        # Primero ver si ya existe para evitar duplicación
        existing = cursor.execute("""
            SELECT id FROM demanda_config 
            WHERE puesto_id = 32 AND tipo_dia = 'Finde_Feriado' 
              AND hora_inicio = '00:00' AND hora_fin = '06:00' AND dias_semana = '5,6'
        """).fetchone()
        
        if not existing:
            cursor.execute("""
                INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max, dias_semana, activo)
                VALUES (32, 'Finde_Feriado', '00:00', '06:00', 0, 0, '5,6', 1)
            """)
            print("Nueva demanda específica insertada en demanda_config.")
        else:
            cursor.execute("""
                UPDATE demanda_config 
                SET cantidad_min = 0, cantidad_max = 0, activo = 1
                WHERE id = ?
            """, (existing[0],))
            print("Demanda específica existente actualizada.")
            
        conn.commit()
        conn.close()
        
        # 4. Ejecutar el solver para el Servicio 4 en Julio 2026
        # Como es una prueba, corremos el comando python main.py --servicio 4 --inicio 2026-07-01 --fin 2026-07-31
        print("Ejecutando el optimizador...")
        cmd = ["python", "main.py", "--servicio", "4", "--inicio", "2026-07-01", "--fin", "2026-07-31"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("Resultado del comando:")
        print(result.stdout)
        if result.stderr:
            print("Errores en ejecución:")
            print(result.stderr)
            
        # 5. Consultar los resultados en la base de datos para las guardias de 00-06_Monitorista en Julio
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Obtener el último cronograma
        crono = cursor.execute("SELECT id FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
        if crono:
            crono_id = crono[0]
            print(f"\nGuardias asignadas en el cronograma ID {crono_id} para '00-06_Monitorista':")
            guardias = cursor.execute("""
                SELECT fecha, nombre, turno 
                FROM guardias 
                WHERE cronograma_id = ? AND turno = '00-06_Monitorista'
                ORDER BY fecha
            """, (crono_id,)).fetchall()
            
            for g in guardias:
                fecha_str = g[0]
                dt = pd.to_datetime(fecha_str)
                dia_semana = dt.day_name()
                print(f"Fecha: {fecha_str} ({dia_semana}), Empleado: {g[1]}, Turno: {g[2]}")
        else:
            print("No se encontró ningún cronograma guardado.")
            
        conn.close()

    finally:
        # 6. Restaurar base de datos
        if os.path.exists(backup_file):
            shutil.copyfile(backup_file, db_file)
            os.remove(backup_file)
            print("Base de datos restaurada al estado original.")
            
if __name__ == "__main__":
    main()
