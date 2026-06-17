import os
import shutil
import subprocess
import sys

db_file = "cronograma_inteligente.db"
temp_db = "cronograma_inteligente_temp.db"

print("Step 1: Copying original DB to temp DB...")
try:
    if os.path.exists(temp_db):
        os.remove(temp_db)
    shutil.copy(db_file, temp_db)
    print("Copy successful.")
    
    # Run the main.py optimization script
    print("Step 2: Running optimizer on temp DB...")
    env = os.environ.copy()
    env["USE_TEMP_DB"] = temp_db
    
    # Forward any arguments passed to this script, or default to service 1
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--servicio", "1", "--inicio", "2026-06-22", "--fin", "2026-07-31"]
    
    result = subprocess.run(
        [sys.executable, "main.py"] + args,
        env=env,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("Optimizer ran successfully.")
        print("Step 3: Copying temp DB back to original...")
        shutil.copy(temp_db, db_file)
        print("Original DB overwritten successfully!")
    else:
        print(f"Optimizer failed with exit code: {result.returncode}")
        
except Exception as e:
    print("Error during temporary execution flow:", e)
finally:
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
            print("Temp DB cleaned up.")
        except Exception as e:
            print("Failed to remove temp DB:", e)
