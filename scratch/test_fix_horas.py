import os
import sys
import shutil

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

min_horas_path = os.path.join(project_root, 'restricciones', 'hard', 'min_horas_mes_calendario.py')
max_horas_path = os.path.join(project_root, 'restricciones', 'hard', 'max_horas_mes_calendario.py')

min_backup = min_horas_path + '.backup'
max_backup = max_horas_path + '.backup'

# Hacer backups
shutil.copyfile(min_horas_path, min_backup)
shutil.copyfile(max_horas_path, max_backup)

try:
    # 1. Modificar min_horas_mes_calendario.py
    with open(min_horas_path, 'r', encoding='utf-8') as f:
        min_content = f.read()
    
    target_loop = "for m_key, dias_m in meses.items():"
    replacement_loop = "for m_key, dias_m in meses.items():\n            if m_key != fecha_inicio_dt.strftime('%Y-%m'):\n                continue"
    
    modified_min = min_content.replace(target_loop, replacement_loop)
    with open(min_horas_path, 'w', encoding='utf-8') as f:
        f.write(modified_min)
        
    # 2. Modificar max_horas_mes_calendario.py
    with open(max_horas_path, 'r', encoding='utf-8') as f:
        max_content = f.read()
        
    modified_max = max_content.replace(target_loop, replacement_loop)
    with open(max_horas_path, 'w', encoding='utf-8') as f:
        f.write(modified_max)
        
    print("Reglas de horas modificadas temporalmente.")
    
    # 3. Ejecutar la optimización
    from main import ejecutar_optimizacion
    res = ejecutar_optimizacion(servicio_id=2, fecha_inicio="2026-08-01", fecha_fin="2026-09-06", modo_debug=False, max_time_in_seconds=30)
    print("Resultado de la optimización con fin en el 06 de septiembre:", res)

finally:
    # Restaurar
    if os.path.exists(min_backup):
        shutil.copyfile(min_backup, min_horas_path)
        os.remove(min_backup)
    if os.path.exists(max_backup):
        shutil.copyfile(max_backup, max_horas_path)
        os.remove(max_backup)
    print("Reglas de horas restauradas.")
