import sqlite3

def run_migrations():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    print("Checking 'licencias' table for 'metadata' column...")
    cursor.execute("PRAGMA table_info(licencias)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'metadata' not in columns:
        print("Adding 'metadata' column to 'licencias' table...")
        cursor.execute("ALTER TABLE licencias ADD COLUMN metadata TEXT")
        print("Column 'metadata' added successfully.")
    else:
        print("Column 'metadata' already exists in 'licencias' table.")

    print("\nChecking for 'Area Medica UTI' service...")
    cursor.execute("SELECT id FROM servicios WHERE nombre = ?", ("Area Medica UTI",))
    service = cursor.fetchone()

    if not service:
        print("Adding 'Area Medica UTI' service...")
        # Assuming (id, organizacion_id, nombre) based on previous check
        # Existing are (1, 1, 'Kinesiologia Critica'), (2, 1, 'Enfermeria UTI')
        cursor.execute("INSERT INTO servicios (organizacion_id, nombre) VALUES (?, ?)", (1, "Area Medica UTI"))
        print(f"Service 'Area Medica UTI' added with ID: {cursor.lastrowid}")
    else:
        print(f"Service 'Area Medica UTI' already exists with ID: {service[0]}")

    conn.commit()
    conn.close()
    print("\nMigrations completed.")

if __name__ == "__main__":
    run_migrations()
