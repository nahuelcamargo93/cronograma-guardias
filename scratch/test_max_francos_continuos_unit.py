import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ortools.sat.python import cp_model
from restricciones.hard.max_francos_continuos import apply
from restricciones.cargador import activar_assumptions

# Mock clases para simular el contexto del motor de OR-Tools
class MockEmpleado:
    def __init__(self, nombre):
        self.nombre = nombre
        self.dias_licencia = set()
        self.reglas = {}

class MockCtx:
    def __init__(self):
        self.dias = 10
        self.fecha_inicio = "2026-07-01"
        self.offset_dia = 3  # Jueves
        self.feriados = set()
        self.demanda_turnos = {"Semana": {"M": 1}, "Finde_Feriado": {"M": 1}}
        self.empleados = []
        self.reglas_servicio = {}
        self.ajustes_reglas_personal = {}
        self.historial_semana_previa = {}
        self.turnos = {}
        self.penalizaciones_soft = []
        
        # Atributos requeridos por restriccion.cargador
        self.modo_debug = False
        self.codigo_regla = "MAX_FRANCOS_CONTINUOS"
        self.assumptions = []
        self.current_assumption = None

def test_modo_hard():
    print("--- Test 1: Modo HARD, max_francos = 2 ---")
    modelo = cp_model.CpModel()
    ctx = MockCtx()
    emp = MockEmpleado("JUAN")
    ctx.empleados.append(emp)
    
    # Registramos la regla en la configuración del servicio
    ctx.reglas_servicio['MAX_FRANCOS_CONTINUOS'] = {"max_francos": 2, "modo": "HARD"}
    
    # Creamos variables de turno (un turno "M" por día)
    for d in range(ctx.dias):
        ctx.turnos[("JUAN", d, "M")] = modelo.NewBoolVar(f"turno_JUAN_d{d}_M")
        
    # Aplicamos la regla
    apply(modelo, ctx)
    
    # Activamos las assumptions creadas por add_hard
    activar_assumptions(modelo, ctx, de_verdad=False)
    
    # Caso A: Intentamos forzar 3 francos seguidos (días 1, 2 y 3)
    # Franco significa que NO trabaja (turno M es 0)
    for d in (1, 2, 3):
        modelo.Add(ctx.turnos[("JUAN", d, "M")] == 0)
        
    solver = cp_model.CpSolver()
    status = solver.Solve(modelo)
    
    print(f"  Status esperado: INFEASIBLE. Status obtenido: {solver.StatusName(status)}")
    assert status == cp_model.INFEASIBLE, "Debería ser inviable tener 3 francos consecutivos con max_francos=2 en modo HARD"
    print("  [OK] Modo HARD funciona correctamente impidiendo excesos.")

def test_modo_soft():
    print("\n--- Test 2: Modo SOFT, max_francos = 2, peso_soft = 5000 ---")
    modelo = cp_model.CpModel()
    ctx = MockCtx()
    emp = MockEmpleado("JUAN")
    ctx.empleados.append(emp)
    
    ctx.reglas_servicio['MAX_FRANCOS_CONTINUOS'] = {"max_francos": 2, "modo": "SOFT", "peso_soft": 5000}
    
    for d in range(ctx.dias):
        ctx.turnos[("JUAN", d, "M")] = modelo.NewBoolVar(f"turno_JUAN_d{d}_M")
        
    apply(modelo, ctx)
    
    # Sumamos las penalizaciones al objetivo
    modelo.Minimize(sum(ctx.penalizaciones_soft))
    
    # Forzamos 4 francos seguidos (días 1, 2, 3, 4) -> 2 ventanas violadas (1-3 y 2-4)
    for d in (1, 2, 3, 4):
        modelo.Add(ctx.turnos[("JUAN", d, "M")] == 0)
        
    solver = cp_model.CpSolver()
    status = solver.Solve(modelo)
    
    print(f"  Status esperado: OPTIMAL. Status obtenido: {solver.StatusName(status)}")
    print(f"  Costo esperado: 10000 (2 violaciones * 5000). Costo obtenido: {solver.ObjectiveValue()}")
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    assert abs(solver.ObjectiveValue() - 10000) < 1e-5, "La penalización debería ser exactamente 10000"
    print("  [OK] Modo SOFT calcula y penaliza correctamente en la función objetivo.")

def test_exclusión_licencia():
    print("\n--- Test 3: Exclusión de Licencias (No cuentan como francos) ---")
    modelo = cp_model.CpModel()
    ctx = MockCtx()
    emp = MockEmpleado("JUAN")
    # Ponemos el día 2 como día de licencia
    emp.dias_licencia.add(2)
    ctx.empleados.append(emp)
    
    ctx.reglas_servicio['MAX_FRANCOS_CONTINUOS'] = {"max_francos": 2, "modo": "HARD"}
    
    for d in range(ctx.dias):
        ctx.turnos[("JUAN", d, "M")] = modelo.NewBoolVar(f"turno_JUAN_d{d}_M")
        
    apply(modelo, ctx)
    
    # Activamos las assumptions creadas por add_hard
    activar_assumptions(modelo, ctx, de_verdad=False)
    
    # Forzamos no trabajar en días 1, 2, 3
    # El día 2 es licencia (es_licencia=1), por ende F[2]=0.
    # Así, no hay 3 francos consecutivos reales (el día 2 es una licencia, interrumpe el conteo).
    for d in (1, 2, 3):
        modelo.Add(ctx.turnos[("JUAN", d, "M")] == 0)
        
    solver = cp_model.CpSolver()
    status = solver.Solve(modelo)
    
    print(f"  Status esperado: OPTIMAL/FEASIBLE. Status obtenido: {solver.StatusName(status)}")
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), "Debería ser viable porque el día de licencia no cuenta como franco"
    print("  [OK] La licencia se excluye y no suma a los francos consecutivos.")

if __name__ == "__main__":
    test_modo_hard()
    test_modo_soft()
    test_exclusión_licencia()
    print("\n¡Todos los tests unitarios pasaron con éxito!")
