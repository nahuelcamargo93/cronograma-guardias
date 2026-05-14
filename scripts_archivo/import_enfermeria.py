import sqlite3

def import_enfermeria():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    try:
        # 1. Create Service
        cursor.execute("INSERT INTO servicios (organizacion_id, nombre) VALUES (1, 'Enfermeria UTI')")
        servicio_id = cursor.lastrowid
        print(f"Service 'Enfermeria UTI' created with ID: {servicio_id}")
        
        # 2. Create a default Puesto for this service
        cursor.execute("INSERT INTO puestos (servicio_id, nombre) VALUES (?, 'UTI')", (servicio_id,))
        puesto_id = cursor.lastrowid
        print(f"Puesto 'UTI' created for service {servicio_id} with ID: {puesto_id}")
        
        # 3. List of personnel
        personnel = [
            "ABELENDA GRISELL", "ALBELO TANIA", "ALCARAZ ELIANA", "ALCARAZ FRANCISO", "ANDREOLI LUCIANA",
            "ARCE DANIEL", "ASTUDILLO MELINA", "BARROSO ERICA", "BASCUR ALEJANDRA", "BORIA MAYRA",
            "CALDERON MARIA JOSE", "CAMPOS PRISCILA", "CARRERAS FLAVIA", "CASTRO LUCIANO", "CORSO ARTURO",
            "CHIRINO CAROLINA", "CORIA LUCIANO", "DOMINGUEZ VERONICA", "DURAN JAZMIN", "ECHENIQUE ROCIO",
            "ESCALANTE CARLA", "ESCUDERO SERGIO", "FERNANDEZ PAOLA", "FERNANDEZ YESICA", "GIMENEZ KAREN",
            "GOMES STHEFANIA", "GOMEZ LOURDES", "GRABOVIECKI FERNANDA", "GUIÑAZU KARINA", "IRAZABAL MARIANGELES",
            "LUCERO MATIAS", "MAÑE LORENA", "MEDINA LAURA", "MIRANDA LUCIANA", "MIRANDA YANINA", "MONDONE PAULA",
            "NIEVAS CARLA", "OLGUIN LUCIA", "ORTIZ LAURA", "PALACIOS FACUNDO", "PALANA GRACIELA", "PEREIRA CRISTINA",
            "POLETTI NATALIA", "QUEVEDO CELESTE", "RINALDINI IVANA", "ROJAS JULIANA", "SOSA NAHUEL", "SUAREZ JESICA",
            "TULA DAIANA", "VELEZ DANIEL", "VELIZ LIONEL", "VERA JULIETA"
        ]
        
        # 4. Insert personnel
        for name in personnel:
            cursor.execute("""
                INSERT INTO personal (nombre, rol, organizacion_id, servicio_id)
                VALUES (?, 'Rotativo', 1, ?)
            """, (name.strip(), servicio_id))
            
        conn.commit()
        print(f"Successfully imported {len(personnel)} personnel members.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_enfermeria()
