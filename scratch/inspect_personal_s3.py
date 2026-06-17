import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import sqlite3
import json

def inspect_personal():
    conn = sqlite3.connect(os.path.join(project_root, "cronograma_inteligente.db"))
    cursor = conn.cursor()
    
    # Obtener el personal con sus puestos habilitados
    cursor.execute("""
        SELECT p.nombre, p.rol, p.categoria,
               (SELECT group_concat(puestos.nombre) FROM personal_puestos pp JOIN puestos ON pp.puesto_id = puestos.id WHERE pp.personal_nombre = p.nombre) as habilitados
        FROM personal p
        WHERE p.servicio_id = 3 AND COALESCE(p.activo, 1) = 1
    """)
    
    plantas = 0
    residentes = 0
    otros = 0
    
    print("=== Empleados y Habilitaciones del Servicio 3 ===")
    for row in cursor.fetchall():
        nombre, rol, categoria, hab = row
        print(f"Nombre: {nombre} | Rol: {rol} | Cat: {categoria} | Habilitados: {hab}")
        
        # Determinar si es Planta o Residente
        if hab:
            habs = [h.strip() for h in hab.split(",")]
            if "Planta" in habs:
                plantas += 1
            elif "Residente" in habs:
                residentes += 1
            else:
                otros += 1
        else:
            if rol == "Planta":
                plantas += 1
            elif rol == "Residente":
                residentes += 1
            else:
                otros += 1
                
    print(f"\nResumen: Planta={plantas}, Residente={residentes}, Otros/Sin Puesto={otros}")
    
    # Calcular piso de horas para Planta y Residente
    # Las horas mínimas de la regla de servicio 3 son 185
    cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    regla_serv = cursor.fetchone()
    min_h_serv = 185
    if regla_serv and regla_serv[0]:
        min_h_serv = json.loads(regla_serv[0]).get("min_horas", 185)
        
    print(f"\nMin Horas Servicio default: {min_h_serv}")
    
    # Cargar ajustes individuales de min_horas
    cursor.execute("""
        SELECT pr.personal_nombre, pr.parametros_json 
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 3 AND pr.codigo_regla = 'MIN_HORAS_MES_CALENDARIO' AND pr.activo = 1
    """)
    ajustes = {row[0]: json.loads(row[1]).get("min_horas", min_h_serv) for row in cursor.fetchall()}
    
    # Volver a recorrer para calcular sumas individuales
    cursor.execute("""
        SELECT p.nombre,
               (SELECT group_concat(puestos.nombre) FROM personal_puestos pp JOIN puestos ON pp.puesto_id = puestos.id WHERE pp.personal_nombre = p.nombre) as habilitados
        FROM personal p
        WHERE p.servicio_id = 3 AND COALESCE(p.activo, 1) = 1
    """)
    
    piso_planta = 0
    piso_residente = 0
    
    for row in cursor.fetchall():
        nombre, hab = row
        piso = ajustes.get(nombre, min_h_serv)
        
        is_planta = False
        is_res = False
        if hab:
            habs = [h.strip() for h in hab.split(",")]
            if "Planta" in habs:
                is_planta = True
            elif "Residente" in habs:
                is_res = True
        
        if is_planta:
            piso_planta += piso
        elif is_res:
            piso_residente += piso
            
    print(f"Suma de pisos mínimos para Planta: {piso_planta} horas")
    print(f"Suma de pisos mínimos para Residente: {piso_residente} horas")
    
    conn.close()

if __name__ == "__main__":
    inspect_personal()
