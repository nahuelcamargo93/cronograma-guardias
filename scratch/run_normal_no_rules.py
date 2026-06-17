import sqlite3
import subprocess

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"

def run_test():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Desactivar temporalmente
    print("Desactivando CUMPLEANOS_LIBRE y DIA_MADRE_PADRE_LIBRE en la DB...")
    cursor.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 1 AND codigo_regla IN ('CUMPLEANOS_LIBRE', 'DIA_MADRE_PADRE_LIBRE')")
    conn.commit()

    try:
        # Correr main.py
        print("Ejecutando python main.py...")
        res = subprocess.run(["python", "main.py"], capture_output=True, text=True)
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)
    finally:
        # Reactivar
        print("Reactivando reglas en la DB...")
        cursor.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 1 AND codigo_regla IN ('CUMPLEANOS_LIBRE', 'DIA_MADRE_PADRE_LIBRE')")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    run_test()
