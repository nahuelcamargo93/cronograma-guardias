import json
import urllib.request
import urllib.parse

def check_structure():
    spreadsheet_id = "11oCu39JKyDCSS9YGkxzZgF6vB9mTJxb8vfbwDNQXPWU"
    pestana = "Enfermeria"
    api_key = "AIzaSyCWPsqv2Ao7-5t5NOGFxo0NPECBnNb4zxA"
    
    rango = urllib.parse.quote(f"'{pestana}'!A:AZ")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{rango}?key={api_key}"
    
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    filas = data.get("values", [])
    
    for r_idx in range(35, min(100, len(filas))):
        if r_idx < len(filas):
            fila = filas[r_idx]
            val0 = str(fila[0]).strip() if len(fila) > 0 else ""
            print(f"Row {r_idx}: Col 0 = '{val0}', len = {len(fila)}, values = {fila[:5]}")

if __name__ == '__main__':
    check_structure()
