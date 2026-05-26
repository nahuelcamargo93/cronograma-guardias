with open('soft_rules.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'modelo.Add' in line:
            print(f"{idx}: {line.strip()}")
