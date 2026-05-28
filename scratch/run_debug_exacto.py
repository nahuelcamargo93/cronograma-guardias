import subprocess
import os

with open("data.py", "r", encoding="utf-8") as f:
    orig_data = f.read()

try:
    # Temporarily change data.py to July 2026
    new_data = orig_data.replace('FECHA_INICIO = "2027-07-01"', 'FECHA_INICIO = "2026-07-01"')
    new_data = new_data.replace('FECHA_FIN    = "2027-07-31"', 'FECHA_FIN    = "2026-07-31"')
    
    with open("data.py", "w", encoding="utf-8") as f:
        f.write(new_data)
        
    print("Running debug_exacto_run.py in subprocess...")
    res = subprocess.run(["python", "scratch/debug_exacto_run.py"], capture_output=True)
    stdout_decoded = res.stdout.decode("utf-8", errors="replace")
    stderr_decoded = res.stderr.decode("utf-8", errors="replace")
    
    with open("scratch/debug_exacto_output.txt", "w", encoding="utf-8") as f_out:
        f_out.write("--- STDOUT ---\n")
        f_out.write(stdout_decoded)
        f_out.write("\n--- STDERR ---\n")
        f_out.write(stderr_decoded)
        
    print("Saved outputs to scratch/debug_exacto_output.txt")
        
finally:
    # Restore orig_data
    with open("data.py", "w", encoding="utf-8") as f:
        f.write(orig_data)
    print("Restored data.py")
