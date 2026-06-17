import os

def search_word(word):
    print(f"Searching for '{word}' in python files:")
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                for encoding in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        with open(path, "r", encoding=encoding) as f:
                            content = f.read()
                            if word.lower() in content.lower():
                                print(f"Found in {path}")
                                break
                    except Exception:
                        pass

if __name__ == '__main__':
    search_word("IIS")
    search_word("infeasible")
    search_word("cerrando")
