import subprocess

print("Ejecutando main.py para Servicio 2 sin modificar la DB...")
result = subprocess.run(
    ["python", "main.py", "--servicio", "2", "--inicio", "2026-08-01", "--crono-base", "583", "--timeout", "10"],
    capture_output=True,
    text=True
)
print("\n=== STDOUT ===")
print(result.stdout)
print("\n=== STDERR ===")
print(result.stderr)
