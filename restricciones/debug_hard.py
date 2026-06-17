"""
restricciones/debug_hard.py — Diagnóstico matemático iterativo (Modo Debug Hard).

Aísla conflictos matemáticos de inviabilidad reconstruyendo selectivamente
el modelo con exclusiones dinámicas de reglas duras y personas.
"""

def ejecutar_diagnostico_hard(empleados, codigos_reglas, resolver_con_exclusiones_cb) -> dict:
    """Ejecuta el diagnóstico iterativo desactivando reglas y personas.

    Utiliza el callback resolver_con_exclusiones_cb para reconstruir y resolver
    el modelo de forma limpia, evitando las limitaciones de las assumptions de CP-SAT.
    """
    print("\n" + "="*70)
    print("  [DEBUG HARD] INICIANDO DIAGNÓSTICO DE INVIABILIDAD MATEMÁTICA")
    print("  Reconstruyendo selectivamente el modelo para aislar el conflicto...")
    print("="*70 + "\n")

    print(f"  [Info] Se analizarán {len(codigos_reglas)} reglas duras activas:")
    for cod in sorted(codigos_reglas):
        print(f"    - {cod}")
    print()

    reglas_conflictivas = {}

    # --- FASE 1: DESACTIVAR REGLAS UNA A UNA ---
    print("  [Fase 1] Evaluando desactivación completa de cada regla...")
    for cod_eval in sorted(codigos_reglas):
        exclusiones = {(cod_eval, None)}
        
        # Resolver con la exclusión activa
        viable = resolver_con_exclusiones_cb(exclusiones)
        
        if viable:
            print(f"    --> [CONTRADICTORIA] Desactivar '{cod_eval}' hace que el modelo sea VIABLE.")
            reglas_conflictivas[cod_eval] = []
        else:
            print(f"    ... Desactivar '{cod_eval}' sigue siendo INVIABLE.")

    # --- FASE 2: DESACTIVAR PERSONAS UNA A UNA PARA CADA REGLA CONFLICTIVA ---
    if reglas_conflictivas:
        print("\n  [Fase 2] Buscando personas responsables en las reglas conflictivas...")
        for cod_conf in reglas_conflictivas.keys():
            print(f"    Analizando responsables para la regla '{cod_conf}':")
            for emp in empleados:
                exclusiones = {(cod_conf, emp.nombre)}
                
                viable = resolver_con_exclusiones_cb(exclusiones)
                
                if viable:
                    print(f"      --> [RESPONSABLE] Desactivar '{cod_conf}' solo para '{emp.nombre}' hace al modelo VIABLE.")
                    reglas_conflictivas[cod_conf].append(emp.nombre)

    # --- REPORTE FINAL ---
    print("\n" + "="*70)
    print("  [DEBUG HARD] RESUMEN DE DIAGNÓSTICO DE CONFLICTOS")
    print("="*70)
    if not reglas_conflictivas:
        print("  No se identificó ninguna regla cuya desactivación individual solucione")
        print("  el conflicto. Es posible que sea una colisión de múltiples reglas simultáneas.")
        print("  Se recomienda usar el modo de relajación Debug Soft.")
    else:
        for cod_conf, personas in reglas_conflictivas.items():
            print(f"\n  REGLA CONFLICTIVA: {cod_conf}")
            if personas:
                print("  Responsables únicos del conflicto (desactivarlo para ellos resuelve la inviabilidad):")
                for p in personas:
                    print(f"    - {p}")
            else:
                print("  La regla causa inviabilidad de forma global o sistémica (no individual).")
    print("\n" + "="*70 + "\n")

    return reglas_conflictivas
