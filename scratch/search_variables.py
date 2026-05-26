with open('hard_rules.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'puesto_nombre' in line or 'puestos_habilitados' in line or 'puesto_id' in line or 'vars' in line:
            print(f"Line {idx}: {line.strip()}")
