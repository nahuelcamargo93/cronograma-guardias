with open('C:/Users/asus/.gemini/antigravity-ide/brain/32706fba-e314-4159-b51c-f8872a341c2e/.system_generated/tasks/task-250.log', 'r') as f:
    lines = f.readlines()

for line in lines:
    if line.startswith("['REG_LICENCIAS'"):
        import ast
        try:
            arr = ast.literal_eval(line.strip())
            print(f"Total conflict elements: {len(arr)}")
            print("Unique prefixes/groups:")
            prefixes = set()
            for x in arr:
                if '__' in x:
                    prefixes.add(x.split('__')[0])
                else:
                    prefixes.add(x)
            for p in sorted(list(prefixes)):
                print(" -", p)
        except Exception as e:
            print("Error parsing line:", e)
