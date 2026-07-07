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
    # 2. Modificar el archivo con las dos condiciones de relajación
    with open(esquema_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar la condición de licencia y de longitud de la semana
    target_licencia = "if licencias_en_bloque == len(days):\n                # Si tiene toda la semana activa de licencia, no forzamos el esquema rígido\n                continue"
    replacement_licencia = "if licencias_en_bloque > 0:\n                # Si tiene algún día de licencia en la semana, no forzamos el esquema rígido\n                continue"
    
    modified_content = content.replace(target_licencia, replacement_licencia)
    
    target_sem = "for (iso_y, iso_w), days in semanas.items():"
    replacement_sem = "for (iso_y, iso_w), days in semanas.items():\n            if len(days) < 4:\n                # Si la semana tiene menos de 4 días en el bloque planificado, omitir\n                continue"
    
    modified_content = modified_content.replace(target_sem, replacement_sem)
    
    with open(esquema_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("Archivo esquema_semanal_enfermeria.py modificado temporalmente.")
    
    # 3. Ejecutar la optimización normal sin debug
    from main import ejecutar_optimizacion
    res = ejecutar_optimizacion(servicio_id=2, fecha_inicio="2026-08-01", fecha_fin="2026-08-31", modo_debug=False, max_time_in_seconds=30)
    print("Resultado de la optimización con la solución completa:", res)

finally:
    # 4. Restaurar el archivo original
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, esquema_path)
        os.remove(backup_path)
        print("Archivo esquema_semanal_enfermeria.py restaurado.")
