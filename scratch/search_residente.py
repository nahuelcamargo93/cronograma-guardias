with open('hard_rules.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'residente' in line.lower() or 'planta' in line.lower():
            print(f"Line {idx}: {line.strip()}")
