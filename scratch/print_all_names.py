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
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    
    df_resultados, df_personal, flrs_asignados = exportar_pdf.obtener_estructuras_reporte(crono_id, fecha_inicio, fecha_fin)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    
    print("=== DF_PERSONAL NAMES ===")
    for n in sorted(df_personal['Nombre'].tolist()):
        print(f"Personal: {repr(n)}")
        
    print("\n=== DF_PERSONA INDEX ===")
    for n in sorted(df_persona.index.tolist()):
        print(f"Persona: {repr(n)}")

if __name__ == '__main__':
    main()
