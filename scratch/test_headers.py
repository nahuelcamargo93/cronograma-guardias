import urllib.request
import urllib.parse
import json

def test():
    api_key = "AIzaSyCWPsqv2Ao7-5t5NOGFxo0NPECBnNb4zxA"
    spreadsheet_id = "1KvMRlYeKNpB5jknQHRnthGJ8g9YUjxYMAn2-iyYUBws"
    
    url_meta = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={api_key}"
    try:
        with urllib.request.urlopen(url_meta) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
        print("Pestañas encontradas:")
        for sheet in meta.get("sheets", []):
            title = sheet["properties"]["title"]
            print(f" - Title (repr): {repr(title)} | Length: {len(title)}")
            
            # Intentar leer la pestaña con su nombre exacto
            rango = urllib.parse.quote(f"'{title}'!A1:E5")
            url_val = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{rango}?key={api_key}"
            try:
                with urllib.request.urlopen(url_val) as resp_val:
                    data = json.loads(resp_val.read().decode("utf-8"))
                print(f"   Valores A1:E5: {data.get('values', [])}")
            except Exception as e_val:
                print(f"   Error al leer: {e_val}")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == '__main__':
    test()
