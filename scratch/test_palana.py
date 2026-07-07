import sqlite3
import subprocess

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Activar el franco forzado de Palana
cursor.execute("UPDATE personal_francos_forzados SET activo = 1 WHERE personal_nombre = 'PALANA GRACIELA' AND fecha_inicio = '2026-08-01'")
print(f"Activado franco de Palana. Filas afectadas: {cursor.rowcount}")
conn.commit()

try:
    # 2. Ejecutar main con debug-hard para servicio 2 y crono-base 583
    print("Ejecutando diagnóstico para Servicio 2 con --crono-base 583...")
    result = subprocess.run(
        ["python", "main.py", "--servicio", "2", "--inicio", "2026-08-01", "--crono-base", "583", "--timeout", "30", "--debug-hard"],
        capture_output=True,
        text=True
    )
    print("\n=== OUTPUT ===")
    print(result.stdout)
    print("\n=== ERROR ===")
    print(result.stderr)
finally:
    # 3. Restaurar activo = 0
    cursor.execute("UPDATE personal_francos_forzados SET activo = 0 WHERE personal_nombre = 'PALANA GRACIELA' AND fecha_inicio = '2026-08-01'")
    conn.commit()
    print("Restaurado franco de Palana a inactivo.")
    conn.close()
