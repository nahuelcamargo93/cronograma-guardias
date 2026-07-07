import sys, os
sys.path.append(os.getcwd())

from database.data_loader import obtener_empleados
import rule_engine as _re

empleados = obtener_empleados(1, "2026-08-01", 31)

for emp in empleados:
    if emp.nombre in ('Toledo, Andrea', 'Garcia, Luciano'):
        fija = emp.reglas.get('ASIGNACION_FIJA', 'NO EXISTE')
        print(f"\n=== {emp.nombre} (rol={emp.rol}) ===")
        print(f"  emp.reglas['ASIGNACION_FIJA'] = {fija}")
        
        # Probar resolver_parametros_regla para un martes (dia 11 agosto = index 10)
        fecha_test = "2026-08-11"
        params = _re.resolver_parametros_regla(
            'ASIGNACION_FIJA', emp.nombre, fecha_test,
            {}, emp.reglas, {}
        )
        print(f"  resolver_parametros_regla('ASIGNACION_FIJA', '{fecha_test}'): {params}")
        print(f"  regla_existe: {_re.regla_existe(params)}")
        print(f"  isinstance list: {isinstance(params, list)}")
