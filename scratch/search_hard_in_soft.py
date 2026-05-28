with open("soft_rules.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print("modelo.Add occurrences in soft_rules.py:")
for idx, line in enumerate(lines):
    if "modelo.Add(" in line:
        print(f"L{idx+1}: {line.strip()}")
