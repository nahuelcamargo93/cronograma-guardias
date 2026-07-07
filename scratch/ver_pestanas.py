import urllib.request
import urllib.error
import urllib.parse
import json

API_KEY = "AIzaSyCWPsqv2Ao7-5t5NOGFxo0NPECBnNb4zxA"
SPREADSHEET_ID = "1_AXtmjIIPlpYMxANiJIJ_rFnHhxpsezcEh5GI8yAy8M"

rango_encoded = urllib.parse.quote("Cronograma!A:A")
url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{rango_encoded}?key={API_KEY}"
try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    filas = data.get("values", [])
    print(f"Leídas {len(filas)} filas de la columna A:")
    for idx, row in enumerate(filas):
        val = row[0] if len(row) > 0 else "<VACIA>"
        print(f"Fila {idx}: '{val}'")
except Exception as e:
    print(f"Error: {e}")
