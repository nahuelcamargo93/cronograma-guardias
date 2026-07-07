import sqlite3
import subprocess

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Activar franco
cursor.execute("UPDATE personal_francos_forzados SET activo = 1 WHERE personal_nombre = 'PALANA GRACIELA' AND fecha_inicio = '2026-08-01'")
conn.commit()
print("DB activada")

try:
    print("Ejecutando main.py...")
    result = subprocess.run(
        ["python", "main.py", "--servicio", "2", "--inicio", "2026-08-01", "--crono-base", "583", "--timeout", "10"],
        capture_output=True,
        text=True
    )
    print("\n=== STDOUT ===")
    print(result.stdout)
    print("\n=== STDERR ===")
    print(result.stderr)
finally:
    # Desactivar franco
    cursor.execute("UPDATE personal_francos_forzados SET activo = 0 WHERE personal_nombre = 'PALANA GRACIELA' AND fecha_inicio = '2026-08-01'")
    conn.commit()
    print("DB restaurada")
    conn.close()
