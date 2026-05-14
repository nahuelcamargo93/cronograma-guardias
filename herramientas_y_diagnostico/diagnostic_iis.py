import main, hard_rules, data
from ortools.sat.python import cp_model
import pandas as pd
from datetime import date, timedelta

def test_feasibility(disabled_rules=None):
    if disabled_rules is None: disabled_rules = []
    
    # Monkey-patching hard_rules to disable specific rules
    original_Add = cp_model.CpModel.Add
    def patched_Add(self, ct):
        # We can't easily filter by "rule name" from CpModel.Add
        # So we have to patch at the hard_rules function level
        return original_Add(self, ct)
    
    # We will use a more surgical approach: replacing rule blocks in hard_rules
    # Actually, let's just use a modified version of aplicar_reglas_duras
    pass

def run_diagnostic():
    print("--- INICIANDO DIAGNÓSTICO DE INVIABILIDAD ---")
    
    rules_to_test = [
        "MAX_HORAS_SEMANA",
        "DESC_POST_NOCHE",
        "UN_TURNO_POR_DIA",
        "MIN_TURNOS",
        "EXCLUIR_TURNOS",
        "ASIGNACION_FIJA"
    ]
    
    # We will run the model multiple times, each time disabling one MORE rule
    # until it becomes FEASIBLE.
    
    current_disabled = []
    for rule in rules_to_test:
        current_disabled.append(rule)
        print(f"Probando desactivando: {current_disabled}")
        
        # We create a script that runs main.py but with these rules commented out in memory
        # Or better, we use global flags if they exist.
        # Let's use a dynamic approach.
        
        # For simplicity, I'll just check the most likely candidates first.
        pass

if __name__ == "__main__":
    # Diagnostic: Check if any MIN_TURNOS is impossible due to exclusions
    import db
    db.inicializar_db()
    rp = db.cargar_reglas_personal(1)
    
    print("\n--- ANALIZANDO CONFLICTOS MIN_TURNOS vs EXCLUIR_TURNOS ---")
    for p, reglas in rp.items():
        if 'MIN_TURNOS' in reglas and 'EXCLUIR_TURNOS' in reglas:
            mins = reglas['MIN_TURNOS']
            excls = reglas['EXCLUIR_TURNOS']
            for m in mins:
                t_min = m.get('turno')
                for e in excls:
                    if t_min in e.get('turnos', []):
                        print(f"!!! CONFLICTO DETECTADO: {p} tiene MIN_TURNOS para '{t_min}' pero lo tiene en EXCLUIR_TURNOS.")

    # Check if Vacantes > Available People on any day
    print("\n--- ANALIZANDO COBERTURA DIARIA ---")
    # ... (already did this manually, but let's automate)
    
run_diagnostic()
