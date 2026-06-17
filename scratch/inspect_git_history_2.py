import subprocess

commits = ["72fb5e4", "b8cd27f", "eb6d257", "8b2490a"]
for c in commits:
    print(f"=== COMMIT {c} ===")
    # List files in this commit
    try:
        files = subprocess.check_output(f"git ls-tree -r --name-only {c}", shell=True, text=True).splitlines()
        for f in files:
            if "rules" in f or "restricciones" in f or "main" in f or "db" in f:
                try:
                    content = subprocess.check_output(f"git show {c}:{f}", shell=True, text=True, stderr=subprocess.DEVNULL)
                    if "largo" in content.lower() or "flr" in content.lower():
                        print(f"  Found in {f}")
                        lines = content.splitlines()
                        for idx, line in enumerate(lines):
                            if "largo" in line.lower() or "flr" in line.lower():
                                print(f"    Line {idx+1}: {line[:100]}")
                except Exception as e:
                    pass
    except Exception as e:
        print(f"Error for commit {c}: {e}")
