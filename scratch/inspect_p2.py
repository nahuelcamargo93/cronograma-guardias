import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
import pandas as pd
import datetime

import exportar_pdf
from reportes.medicos import exportar_excel_vista_personal

def main():
    crono_id = 152
    datos = exportar_pdf.obtener_datos_cronograma(crono_id)
    if not datos:
        print("No se encontraron datos.")
        return
        
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    
    df_resultados, df_personal, flrs_asignados = exportar_pdf.obtener_estructuras_reporte(crono_id, fecha_inicio, fecha_fin)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    
    print("=== VISTA DE PERSONAL (PAGINA 2) ===")
    for nombre in df_persona.index:
        if "Garcia" in nombre or "Nez" in nombre or "N\u00faez" in nombre or "N\u00f1ez" in nombre:
            print(f"Nombre: {nombre}")
            print(f"  13-Jun (2026-06-13): {df_persona.at[nombre, '2026-06-13']}")
            print(f"  15-Jun (2026-06-15): {df_persona.at[nombre, '2026-06-15']}")

if __name__ == '__main__':
    main()
