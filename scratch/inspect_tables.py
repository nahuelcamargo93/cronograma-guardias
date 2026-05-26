import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # List all tables
    print("=== TABLES ===")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for t in tables:
        print("Table:", t[0])
        # Print schema for the table if it looks like rules or assignments
        if 'reglas' in t[0] or 'ajustes' in t[0] or 'asignacion' in t[0] or 'fija' in t[0]:
            print(f"\nSchema for {t[0]}:")
            schema = cursor.execute(f"PRAGMA table_info({t[0]})").fetchall()
            for col in schema:
                print(f"  Col: {col[1]} | Type: {col[2]}")
                
    conn.close()

if __name__ == '__main__':
    main()
