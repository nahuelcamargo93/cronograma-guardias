import database
from database import queries
import sys

print("Checking dictionary references...")
# Inicializar
queries.init_licencias()

same_lar = (database.LAR is queries.LAR)
same_lpp = (database.LPP is queries.LPP)
same_lm  = (database.LM is queries.LM)

print(f"LAR reference same? {same_lar}")
print(f"LPP reference same? {same_lpp}")
print(f"LM reference same? {same_lm}")

if not (same_lar and same_lpp and same_lm):
    print("ERROR: Stale references detected!")
    sys.exit(1)
else:
    print("SUCCESS: References are synchronized.")
    
print(f"LAR content: {len(database.LAR)} items")
print(f"LPP content: {len(database.LPP)} items")
print(f"LM content: {len(database.LM)} items")
