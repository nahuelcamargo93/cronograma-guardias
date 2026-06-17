import re
import os

username = os.getlogin()
log_path = f"C:/Users/{username}/.gemini/antigravity-ide/brain/1f4ab7af-f31b-4e66-b8be-af78a6d4ae50/.system_generated/tasks/task-23.log"
if not os.path.exists(log_path):
    log_path = "C:/Users/asus/.gemini/antigravity-ide/brain/1f4ab7af-f31b-4e66-b8be-af78a6d4ae50/.system_generated/tasks/task-23.log"

print(f"Leyendo log de path: {log_path}")
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    matches = list(re.finditer(r"\[WARNING\] CONFLICTO MATEM", content))
    if matches:
        print("Bloque de conflicto encontrado:")
        start_idx = matches[-1].start()
        end_idx = content.find("=====", start_idx + 100)
        if end_idx == -1:
            end_idx = start_idx + 2000
        text = content[start_idx:end_idx+5]
        # Limpiar caracteres unicode conflictivos
        clean_text = text.encode('ascii', errors='replace').decode('ascii')
        print(clean_text)
    else:
        print("No se encontro bloque de conflicto.")
else:
    print("El archivo no existe.")
