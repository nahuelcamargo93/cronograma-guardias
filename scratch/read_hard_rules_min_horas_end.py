with open("hard_rules.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx in range(750, 780):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx]}", end="")
