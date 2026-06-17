import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import rule_engine as _re
from database.data_loader import obtener_empleados

def main():
    db.init_licencias(2)
    empleados = obtener_empleados(2, "2026-07-01", 31)
    
    # Buscar a POLETTI NATALIA
    poletti = next((e for e in empleados if "POLETTI" in e.nombre), None)
    if not poletti:
        print("No se encontró a POLETTI NATALIA")
        return
        
    print(f"Empleado: {poletti.nombre}")
    print(f"Regimen: {poletti.regimen_trabajo}")
    print(f"Reglas personales cargadas en Empleado.reglas: {poletti.reglas}")
    
    reglas_servicio = db.cargar_reglas_servicio(2)
    ajustes_reglas_personal = db.cargar_ajustes_reglas_personal("2026-07-01", "2026-07-31")
    
    params = _re.resolver_parametros_regla(
        'MANEJO_FINDES', poletti.nombre, "2026-07-01",
        reglas_servicio, poletti.reglas, ajustes_reglas_personal
    )
    
    print(f"Params resueltos para MANEJO_FINDES: {params}")
    print(f"¿Suspendida?: {_re.regla_suspendida(params)}")

if __name__ == '__main__':
    main()
