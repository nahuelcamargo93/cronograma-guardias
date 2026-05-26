import sys
import os
sys.path.append(os.path.abspath("."))
import debug_imposibilidad

print("--- Running Diagnostic for June 2026 (Service 4) ---")
debug_imposibilidad.reportar_imposibilidad(4, "2026-06-01", "2026-06-30")
