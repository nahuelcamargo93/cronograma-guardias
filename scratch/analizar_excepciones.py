import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    nombres = [
        "Garcia Rodriguez, Maria Eugenia",
        "Aguilera, Graciela",
        "Barloa, Matías Damián",
        "Godoy, Maria",
        "Quintero, Anabela Belen"
    ]
    
    print("--- ESTADO EN LA TABLA personal ---")
    for nom in nombres:
        row = cursor.execute("SELECT nombre, servicio_id, activo, rol, categoria FROM personal WHERE nombre LIKE ?", (f"%{nom.split(',')[0]}%",)).fetchone()
        if row:
            print(f"Nombre DB: {row[0]} | Servicio: {row[1]} | Activo: {row[2]} | Rol: {row[3]} | Cat: {row[4]}")
        else:
            print(f"No encontrado en personal: {nom}")
            
    print("\n--- REGLAS INDIVIDUALES ACTIVAS PARA ESTOS PROFESIONALES ---")
    placeholders = ",".join("?" for _ in nombres)
    # Buscaremos por like para ser mas flexibles con los nombres
    rows_reg = cursor.execute("""
        SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
        FROM personal_reglas pr
        WHERE pr.activo = 1
    """).fetchall()
    
    for row in rows_reg:
        for nom in nombres:
            if nom.split(',')[0] in row[0]:
                print(f"Personal: {row[0]} | Regla: {row[1]} | Params: {row[2]} | Activo: {row[3]}")
                
    print("\n--- AJUSTES INDIVIDUALES PARA JULIO 2026 ---")
    rows_aj = cursor.execute("""
        SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
        FROM personal_reglas_ajustes pra
        WHERE pra.fecha_inicio <= '2026-07-31' AND pra.fecha_fin >= '2026-07-01' AND pra.activo = 1
    """).fetchall()
    for row in rows_aj:
        print(f"Personal: {row[0]} | Regla: {row[1]} | Rango: {row[2]} a {row[3]} | Accion: {row[4]} | Params: {row[5]} | Activo: {row[6]}")
        
    conn.close()

if __name__ == "__main__":
    main()
