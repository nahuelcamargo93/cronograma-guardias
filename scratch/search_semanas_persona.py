with open("soft_rules.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "semanas_M_persona" in line:
            print(f"{i}: {line.strip()}")
