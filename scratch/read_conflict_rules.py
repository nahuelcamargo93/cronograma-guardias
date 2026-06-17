import re

log_path = "C:/Users/asus/.gemini/antigravity-ide/brain/531c7dea-d16c-4089-9be1-b7d4216712cc/.system_generated/tasks/task-139.log"

def main():
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print("Error al abrir log:", e)
        return

    print("Total de líneas leídas:", len(lines))

    # Buscar conflictos (las líneas que empiezan con "   -> REG_")
    conflict_lines = []
    in_conflict_section = False
    for line in lines:
        if "Reglas que hacen el cronograma inviable:" in line:
            in_conflict_section = True
            continue
        if in_conflict_section:
            if line.strip().startswith("="):
                in_conflict_section = False
                continue
            if "->" in line:
                conflict_lines.append(line.strip())

    print(f"\nSe encontraron {len(conflict_lines)} reglas en el conflicto.")
    
    # Filtrar conflictos relacionados con MAX_FRANCOS_SEMANA
    mfs_conflicts = [c for c in conflict_lines if "MAX_FRANCOS_SEMANA" in c]
    print(f"\nConflictos de MAX_FRANCOS_SEMANA ({len(mfs_conflicts)}):")
    for c in mfs_conflicts[:20]:
        print(" ", c)

    # Imprimir algunos otros conflictos para entender qué está pasando
    print("\nOtros conflictos de ejemplo:")
    for c in conflict_lines[:15]:
        print(" ", c)

if __name__ == '__main__':
    main()
