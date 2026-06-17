import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    nombres = [
        "Barloa, Matías Damián",
        "Godoy, Maria",
        "Quintero, Anabela Belen",
        "Garcia Rodriguez, Maria Eugenia",
        "Aguilera, Graciela"
    ]
    
    print("--- DETALLES EN TABLA personal ---")
    for nom in nombres:
        row = cursor.execute("""
            SELECT nombre, servicio_id, activo, rol, categoria 
            FROM personal 
            WHERE nombre = ?
        """, (nom,)).fetchone()
        if row:
            print(f"Nombre: {row[0]} | Servicio: {row[1]} | Activo: {row[2]} | Rol: {row[3]} | Categoria: {row[4]}")
            # Puestos habilitados
            puestos = cursor.execute("""
                SELECT p.nombre 
                FROM personal_puestos pp
                JOIN puestos p ON pp.puesto_id = p.id
                WHERE pp.personal_nombre = ?
            """, (nom,)).fetchall()
            print(f"  Puestos: {[p[0] for p in puestos]}")
        else:
            print(f"No encontrado: {nom}")
            
    conn.close()

if __name__ == "__main__":
    main()
