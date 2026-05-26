import sys
sys.path.append(".")
import main
import pandas as pd
import sqlite3

def main_test():
    print("Ejecutando optimización para Servicio 3 (Médicos UTI) - Junio 2026...")
    res = main.ejecutar_optimizacion(3, "2026-06-01", "2026-06-30", notas="Test de Priorizacion de Residentes")
    
    if not isinstance(res, dict) or res.get("status") != "success":
        print("Error o inviabilidad en la optimización:", res)
        return
        
    cronograma_id = res["cronograma_id"]
    print(f"\nOptimización exitosa. Cronograma ID: {cronograma_id}. Analizando asignaciones de Planta hechas a residentes...")
    
    conn = sqlite3.connect("cronograma_inteligente.db")
    
    # Cargar las guardias generadas
    df_resultados = pd.read_sql_query(f"""
        SELECT fecha as Fecha, turno as Turno, nombre as Personal
        FROM guardias
        WHERE cronograma_id = {cronograma_id}
    """, conn)
    
    # Cargar las categorías y roles de la tabla personal
    df_personal = pd.read_sql_query("SELECT nombre, rol, categoria FROM personal WHERE servicio_id = 3", conn)
    
    # Combinar resultados con datos del personal
    df_merged = df_resultados.merge(df_personal, left_on="Personal", right_on="nombre", how="left")
    
    # Filtrar por turnos de Planta (D_Planta, N_Planta, G_Planta) y rol Residente
    df_planta_residents = df_merged[
        (df_merged["Turno"].str.contains("Planta", case=False)) & 
        (df_merged["rol"] == "Residente")
    ]
    
    if df_planta_residents.empty:
        print("No hay residentes asignados a puestos de Planta en esta solución.")
    else:
        print("\n=== RESIDENTES ASIGNADOS A PLANTA ===")
        print(df_planta_residents[["Fecha", "Turno", "Personal", "categoria"]].to_string(index=False))
        
        print("\n=== RESUMEN DE ASIGNACIONES A PLANTA POR PERSONA Y CATEGORIA ===")
        summary = df_planta_residents.groupby(["Personal", "categoria"]).size().reset_index(name="Cantidad Guardias Planta")
        print(summary.to_string(index=False))
        
    # Mostrar también el total de guardias de Planta cubiertas por médicos de Planta vs Residentes para comparar
    df_planta_all = df_merged[df_merged["Turno"].str.contains("Planta", case=False)]
    print("\n=== TOTAL DE GUARDIAS PLANTA POR ROL ===")
    summary_roles = df_planta_all.groupby("rol").size().reset_index(name="Cantidad Guardias")
    print(summary_roles.to_string(index=False))
    
    conn.close()

if __name__ == '__main__':
    main_test()
