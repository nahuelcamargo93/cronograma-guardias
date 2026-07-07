import os
import sys
import shutil

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

esquema_path = os.path.join(project_root, 'restricciones', 'hard', 'esquema_semanal_enfermeria.py')
backup_path = esquema_path + '.backup'

# 1. Hacer backup del archivo original
shutil.copyfile(esquema_path, backup_path)

try:
    # 2. Modificar el archivo para omitir semanas con menos de 3 días en el bloque
    with open(esquema_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Insertar la condición de len(days) < 3
    target_str = "for (iso_y, iso_w), days in semanas.items():"
    replacement_str = "for (iso_y, iso_w), days in semanas.items():\n            if len(days) < 3:\n                continue"
    
    modified_content = content.replace(target_str, replacement_str)
    
    with open(esquema_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("Archivo esquema_semanal_enfermeria.py modificado temporalmente.")
    
    # 3. Ejecutar la optimización
    from main import ejecutar_optimizacion
    res = ejecutar_optimizacion(servicio_id=2, fecha_inicio="2026-08-01", fecha_fin="2026-08-31", modo_debug=False, max_time_in_seconds=30)
    print("Resultado de la optimización con la solución tentativa:", res)

finally:
    # 4. Restaurar el archivo original
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, esquema_path)
        os.remove(backup_path)
        print("Archivo esquema_semanal_enfermeria.py restaurado.")
