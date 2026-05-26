import re

log_path = r"C:\Users\asus\.gemini\antigravity-ide\brain\bebb27b7-d01c-46c6-a8cc-00ac0b558d33\.system_generated\tasks\task-591.log"

with open(log_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "Probando con" in line or "RESULTADO:" in line:
            print(f"Line {i}: {line.strip()}")
