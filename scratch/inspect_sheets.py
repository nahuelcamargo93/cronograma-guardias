import json
import urllib.request
import urllib.parse

api_key = "AIzaSyCWPsqv2Ao7-5t5NOGFxo0NPECBnNb4zxA"
spreadsheet_id = "1KxwO0ND3TLswzlBJl-MkuTAbxBzWSZAt_V50vwjZMXM"

url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={api_key}"
try:
    with urllib.request.urlopen(url, timeout=15) as resp:
        meta = json.loads(resp.read().decode("utf-8"))
    
    print("Pestañas del Spreadsheet DEFAULT:")
    for sheet in meta.get("sheets", []):
        print(f" - {sheet.get('properties', {}).get('title')}")
except Exception as e:
    print("Error:", e)
