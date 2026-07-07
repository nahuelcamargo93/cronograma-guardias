import json
import urllib.request
import urllib.parse

def check_sheet():
    spreadsheet_id = "11oCu39JKyDCSS9YGkxzZgF6vB9mTJxb8vfbwDNQXPWU"
    pestana = "Enfermeria"
    api_key = "AIzaSyCWPsqv2Ao7-5t5NOGFxo0NPECBnNb4zxA"
    
    rango = urllib.parse.quote(f"'{pestana}'!A:AZ")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{rango}?key={api_key}"
    
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    filas = data.get("values", [])
    print(f"Total rows fetched: {len(filas)}")
    
    # Print the first 35 rows (up to 15 columns each)
    for r_idx in range(min(35, len(filas))):
        fila = filas[r_idx]
        # Pad row to make it readable
        row_str = ", ".join([f"{col_idx}:'{val}'" for col_idx, val in enumerate(fila[:25])])
        print(f"Row {r_idx}: {row_str}")

if __name__ == '__main__':
    check_sheet()
