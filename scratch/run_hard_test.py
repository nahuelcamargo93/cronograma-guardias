import sqlite3
import subprocess

# 1. Set the rule to HARD and active
conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()
c.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = '{"modo": "HARD", "distancias": {"N": 3, "TN": 3}}', activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'DISTANCIA_MINIMA_TIPO_SEMANA'
""")
conn.commit()
conn.close()
print("Regla configurada en modo HARD y activa.")

# 2. Run the solver using main.py with --debug-hard
try:
    print("Ejecutando optimización con debug-hard...")
    result = subprocess.run(
        ["python", "main.py", "--servicio", "2", "--inicio", "2026-08-01", "--debug-hard"],
        capture_output=True, text=True, timeout=300
    )
    print("OUTPUT:")
    print(result.stdout)
    print("ERROR:")
    print(result.stderr)
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
