import sys
import os

# Asegurar que la raíz del proyecto está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import ejecutar_optimizacion

def main():
    # Run optimization without debug to see if it solves normally
    print("Ejecutando optimizacion SIN brecha diaria (ya que brecha diaria es soft ahora, pero queremos ver si el modelo base es feasible y rapido)...")
    import time
    start = time.time()
    # Let's temporarily disable brecha_diaria_personal by monkeypatching the rules list
    import restricciones.double
    if "restricciones.hard.brecha_diaria_personal" in restricciones.double.REGLAS_DOUBLE:
        restricciones.double.REGLAS_DOUBLE.remove("restricciones.hard.brecha_diaria_personal")
        
    res = ejecutar_optimizacion(servicio_id=2, fecha_inicio="2026-07-01", fecha_fin="2026-07-31", notas="Test sin brecha", modo_debug=False)
    print("Resultado:", res)
    print(f"Tiempo transcurrido: {time.time() - start:.2f} segundos")

if __name__ == '__main__':
    main()
