with open("db.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "def cargar_guardias_previas" in line:
            print(f"{i}: {line.strip()}")
