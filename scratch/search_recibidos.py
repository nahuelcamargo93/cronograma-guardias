import os

for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or '.gemini' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'recibidos' in content.lower():
                        print(f"Found in {path}")
            except Exception:
                pass
