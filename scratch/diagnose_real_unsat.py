import sys
import os

sys.path.append(os.path.abspath('.'))

import scratch.diagnose_unsat as du

print("\n--- Running diagnosis directly on the main database ---")
du.reportar_imposibilidad(3, "2026-06-01", "2026-06-30")
