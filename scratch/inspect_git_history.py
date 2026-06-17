import subprocess

commits = ["72fb5e4", "b8cd27f", "eb6d257", "8b2490a"]
for c in commits:
    print(f"=== COMMIT {c} ===")
    for filename in ["hard_rules.py", "soft_rules.py"]:
        try:
            content = subprocess.check_output(f"git show {c}:{filename}", shell=True, text=True, stderr=subprocess.DEVNULL)
            if "FINDE_LARGO" in content:
                print(f"  Found FINDE_LARGO in {filename} of commit {c}")
                # print first few lines of match
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    if "FINDE_LARGO" in line:
                        print(f"    Line {idx+1}: {line}")
        except Exception as e:
            pass
