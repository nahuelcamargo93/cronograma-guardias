from ortools.sat.python import cp_model

def test():
    modelo = cp_model.CpModel()
    var_bloque = modelo.NewBoolVar('var_bloque')
    
    # Simular flr_conds con una constante y un BoolVar
    c0 = modelo.NewConstant(0)
    b1 = modelo.NewBoolVar('b1')
    
    flr_conds = [c0, b1]
    
    literales = []
    for v in flr_conds:
        if hasattr(v, 'Not'):
            literales.append(v.Not())
        else:
            literales.append(v == 0)
            
    print("Literales creados:", [type(x) for x in literales])
    try:
        modelo.AddBoolOr(literales).OnlyEnforceIf(var_bloque.Not())
        print("AddBoolOr ejecutado con éxito")
    except Exception as e:
        print("Error en AddBoolOr:", e)
        return
        
    solver = cp_model.CpSolver()
    status = solver.Solve(modelo)
    print("Solver status:", solver.StatusName(status))

test()
