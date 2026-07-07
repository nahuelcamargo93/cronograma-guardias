import sys
import os
import openpyxl

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from importar_cronograma_sheets import (
    procesar_vista_cronograma,
    construir_mapa_personal,
    resolver_nombre_personal,
    resolver_nombre_turno
)
from database import queries as db_queries
from database.connection import get_connection

def main():
    excel_path = os.path.join(PROJECT_ROOT, "Cronograma_Area_Medica_UTI_Julio26.xlsx")
    if not os.path.exists(excel_path):
        print(f"Error: No existe el archivo {excel_path}")
        return

    print("Cargando libro excel local...")
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb["Cronograma"]
    
    filas = []
    for row in sheet.iter_rows(values_only=True):
        # Convertir None a cadena vacía
        filas.append([str(cell).strip() if cell is not None else "" for cell in row])
        
    print(f"Leídas {len(filas)} filas del Excel local.")
    
    servicio_id = 3
    fecha_inicio = "2026-07-01"
    
    mapa_personal = construir_mapa_personal(servicio_id)
    siglas_map = db_queries.obtener_siglas_turnos(servicio_id)
    siglas_invertido = {sigla.lower(): nombre for nombre, sigla in siglas_map.items()}
    
    with get_connection() as conn:
        rows_turnos = conn.execute("SELECT nombre FROM turnos_config WHERE servicio_id = ?", (servicio_id,)).fetchall()
    nombres_turnos = [r[0] for r in rows_turnos]
    turnos_normalizados = {t.lower(): t for t in nombres_turnos}
    
    with get_connection() as conn:
        personal_db = db_queries.obtener_personal_db(servicio_id)
    mapa_roles = {p['Nombre']: p['Rol'] for p in personal_db}
    
    try:
        from importar_cronograma_sheets import procesar_vista_cronograma as proc_v
        guardias = proc_v(
            filas, servicio_id, fecha_inicio,
            mapa_personal, siglas_invertido, turnos_normalizados,
            nombres_turnos, mapa_roles
        )
        print(f"\n[OK] Parseo local completado con éxito.")
        print(f"Se decodificaron {len(guardias)} guardias de trabajo.")
        
        # Mostrar las primeras 10 guardias para validar
        print("\nMuestra de las primeras 10 guardias decodificadas:")
        for g in guardias[:10]:
            print(f"  Fecha: {g['Fecha']} | Turno: {g['Turno']:20s} | Personal: {g['Personal']}")
            
        # Contar por turno
        conteo_turnos = {}
        for g in guardias:
            conteo_turnos[g['Turno']] = conteo_turnos.get(g['Turno'], 0) + 1
        print("\nConteo por turno:")
        for t, count in conteo_turnos.items():
            print(f"  {t:20s}: {count}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
