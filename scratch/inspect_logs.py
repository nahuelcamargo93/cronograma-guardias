with open("logs_y_debug/output.txt", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
print("=== output.txt (Last 50 lines) ===")
for line in lines[-50:]:
    print(line, end="")

try:
    with open("logs_y_debug/debug_output.txt", "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print("\n=== debug_output.txt (Last 50 lines) ===")
    for line in lines[-50:]:
        print(line, end="")
except FileNotFoundError:
    pass
