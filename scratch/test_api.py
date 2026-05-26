import urllib.request
import json

try:
    url = "http://127.0.0.1:8000/api/reglas/1"
    print(f"Haciendo request a {url}...")
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
        data = json.loads(html)
        print("Respuesta recibida con éxito!")
        print("Reglas generales:", list(data.get("reglas_generales", {}).keys()))
        print("Puestos:", len(data.get("puestos", [])))
        print("Turnos:", len(data.get("turnos", [])))

    url_cat = "http://127.0.0.1:8000/api/reglas_catalogo/1"
    print(f"\nHaciendo request a {url_cat}...")
    with urllib.request.urlopen(url_cat) as response:
        html = response.read().decode('utf-8')
        data_cat = json.loads(html)
        print("Respuesta recibida con éxito!")
        print("Total de reglas en el catálogo:", len(data_cat))
        print("Ejemplo de reglas activas:")
        for r in data_cat[:5]:
            print(f"  - {r.get('codigo_regla')}: Activa={r.get('activa')}")
except Exception as e:
    print(f"Error al conectar/consultar API: {e}")
