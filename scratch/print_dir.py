import sys
sys.path.insert(0, '.')
from ortools.sat.python import cp_model
model = cp_model.CpModel()
proto = model.Proto()
# Añadir una restricción dummy
model.Add(1 == 1)
c = proto.constraints[0]
print("Type of c:", type(c))
print("Dir of c:", dir(c))
