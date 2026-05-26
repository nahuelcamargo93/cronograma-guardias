import os
import glob
import datetime

files = glob.glob("**/*.log", recursive=True) + glob.glob("**/*.txt", recursive=True)
for f in files:
    if "venv" in f or ".git" in f:
        continue
    stat = os.stat(f)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
    print(f"{f}: size={stat.st_size} bytes, mtime={mtime}")
