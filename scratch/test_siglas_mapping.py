import sys
import os

# Agregar la raíz del workspace al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.schema import inicializar_db
from database.connection import get_connection
from database.queries import obtener_siglas_turnos

def main():
    print("Iniciando inicialización de la base de datos...")
    inicializar_db()
    print("Base de datos inicializada correctamente.")

    print("\nVerificando los turnos en la base de datos:")
    print("-" * 60)
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT servicio_id, nombre, sigla 
            FROM turnos_config 
            ORDER BY servicio_id, nombre
        """).fetchall()
        
        for r in rows:
            print(f"Servicio: {r[0]} | Turno: {r[1]:<20} | Sigla: {r[2]}")
    
    print("-" * 60)
    print("\nProbando obtener_siglas_turnos para cada servicio:")
    for s_id in [1, 2, 3, 4]:
        siglas = obtener_siglas_turnos(s_id)
        print(f"Servicio {s_id}: {siglas}")
        
    print("\n¡Verificación finalizada con éxito!")

if __name__ == "__main__":
    main()
