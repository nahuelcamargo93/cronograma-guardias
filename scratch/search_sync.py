import os

target1 = "personal_asignaciones_fijas"
target2 = "personal_reglas_ajustes"

for root, dirs, files in os.walk("."):
    if "venv" in root or ".git" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if target1 in content and target2 in content:
                        print("Found both in:", path)
            except Exception:
                pass
print("Search completed.")
