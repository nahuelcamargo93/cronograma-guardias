import sqlite3
import os
import sys

# Ajustar path por si acaso
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    db_path = os.path.join(PROJECT_ROOT, "cronograma_inteligente.db")
    if not os.path.exists(db_path):
        print(f"No se encontró la base de datos en: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Traer todos los empleados activos, su servicio y el conteo de puestos en personal_puestos
    query = """
        SELECT p.nombre, s.nombre as servicio, p.rol, COUNT(pp.puesto_id) as cant_puestos
        FROM personal p
        JOIN servicios s ON p.servicio_id = s.id
        LEFT JOIN personal_puestos pp ON p.nombre = pp.personal_nombre
        WHERE COALESCE(p.activo, 1) = 1
        GROUP BY p.nombre
        ORDER BY s.nombre, p.nombre
    """

    try:
        rows = cursor.execute(query).fetchall()
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        conn.close()
        return

    sin_puestos = []
    con_puestos = []

    for nombre, servicio, rol, cant in rows:
        if cant == 0:
            sin_puestos.append((nombre, servicio, rol))
        else:
            con_puestos.append((nombre, servicio, rol, cant))

    print("=" * 70)
    print(f"RESULTADO DE LA INSPECCIÓN DE 'personal_puestos'")
    print("=" * 70)
    print(f"Total empleados activos analizados: {len(rows)}")
    print(f"Empleados CON puestos configurados: {len(con_puestos)}")
    print(f"Empleados SIN puestos configurados (caerán en fallback): {len(sin_puestos)}")
    print("-" * 70)

    if sin_puestos:
        print("Detalle de empleados SIN puestos configurados:")
        current_service = None
        for nombre, servicio, rol in sin_puestos:
            if servicio != current_service:
                current_service = servicio
                print(f"\nServicio: {servicio}")
            print(f"  - {nombre} (Rol actual en personal: '{rol}')")
    else:
        print("¡Excelente! Todos los empleados activos tienen al menos un puesto configurado.")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    main()
