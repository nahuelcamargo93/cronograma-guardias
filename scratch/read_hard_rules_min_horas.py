with open("hard_rules.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

found = False
for idx, line in enumerate(lines):
    if "_aplicar_min_horas_mes_calendario" in line and "def " in line:
        print(f"Found on line {idx+1}:")
        for j in range(max(0, idx-5), min(len(lines), idx+40)):
            print(f"{j+1}: {lines[j]}", end="")
        found = True
        break
