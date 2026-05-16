import sqlite3

# Data extracted from the image
data = {
    "Aguilera Graciela": 144,
    "Arias Guillermina": 144,
    "Baracat Denisse": 144,
    "Barloa Matías Damián": 24,
    "Diaz Villafañe Morales Abigail": 144,
    "Garcia Rodriguez, Maria Eugenia.": 144,
    "Godoy Maria": 24,
    "Kolarik Jorge Luis": 144,
    "Silva, Martín Enrique": 144,
    "Mora, Sergio Enrique": 144,
    "Motta, Mayra Belen": 144,
    "Moya, Pedro": 144,
    "Murillo, Santiago": 144,
    "Navarro Suarez Gabriela Belén": 144,
    "Nesteruk María Silvia": 144,
    "Noriega Claudio Martín": 144,
    "Pregot Analia Mariana": 144,
    "Quintero Anabela Belen": 48,
    "Quiroga Sassu Maria Macarena": 144,
    "Sánchez Reinoso Ana Belén": 144,
    "Zeballos Valeria Alejandra": 144,
    "Arce Carolina": 144,
    "Pacheco Celeste": 144,
    "Biscarra Joaquín Martin": 96,
    "Villegas Oliva Maria Belén": 96,
    "Matricadi Wendy Ailen": 96,
    "Núñez Florencia Natalia": 96,
    "Palermo Agustín": 96
}

def update_personal_hours():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Apply schema initialization first to ensure column exists
    import database.schema as schema
    schema.inicializar_db()
    
    print("Updating horas_mensuales_reglamentarias...")
    count = 0
    for nombre, horas in data.items():
        cursor.execute("""
            UPDATE personal 
            SET horas_mensuales_reglamentarias = ? 
            WHERE nombre = ?
        """, (horas, nombre))
        if cursor.rowcount > 0:
            print(f"Updated {nombre}: {horas}")
            count += 1
        else:
            # Try fuzzy match if exact match fails
            cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE ?", (f"%{nombre.split()[0]}%",))
            matches = cursor.fetchall()
            print(f"FAILED to update '{nombre}'. Possible matches: {matches}")
            
    conn.commit()
    conn.close()
    print(f"\nFinished. Updated {count} records.")

if __name__ == "__main__":
    update_personal_hours()
