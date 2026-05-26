import glob

def find_dias_semana():
    files = glob.glob("*.py") + glob.glob("database/*.py")
    for f in files:
        with open(f, "r", encoding="utf-8", errors="ignore") as file:
            content = file.readlines()
            for idx, line in enumerate(content):
                if "dias_semana" in line or "Dias_Habilitados" in line:
                    print(f"File: {f} | Line {idx+1}: {line.strip()}")

if __name__ == '__main__':
    find_dias_semana()
