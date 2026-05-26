with open('soft_rules.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'residente' in line.lower() or 'planta' in line.lower() or 'puesto' in line.lower() or 'rol' in line.lower():
            print(f"Line {idx}: {line.strip()}")
