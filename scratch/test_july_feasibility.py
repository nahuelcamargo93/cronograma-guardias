import sys
import os
sys.path.append(os.getcwd())

import data
data.FECHA_INICIO = "2026-07-01"
data.FECHA_FIN = "2026-07-31"
data.SERVICIO_ID = 2

import scratch.test_feasibility_hard_only as test_feasibility
test_feasibility.main()
