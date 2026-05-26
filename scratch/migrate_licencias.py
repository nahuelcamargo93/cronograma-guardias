import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='licencias'")
    table_sql = cursor.fetchone()[0]
    print('Current SQL:', table_sql)
    if 'CM' not in table_sql:
        print('Migrating licencias table...')
        cursor.execute('PRAGMA foreign_keys = OFF')
        cursor.execute('BEGIN TRANSACTION')
        try:
            cursor.execute('ALTER TABLE licencias RENAME TO licencias_old')
            cursor.execute('''
                CREATE TABLE licencias (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre       TEXT NOT NULL REFERENCES personal(nombre),
                    tipo         TEXT NOT NULL CHECK(tipo IN ('LPP', 'LAR', 'CM', 'LM')),
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin    TEXT NOT NULL,
                    metadata     TEXT
                )
            ''')
            cursor.execute('INSERT INTO licencias (id, nombre, tipo, fecha_inicio, fecha_fin, metadata) SELECT id, nombre, tipo, fecha_inicio, fecha_fin, metadata FROM licencias_old')
            cursor.execute('DROP TABLE licencias_old')
            cursor.execute('COMMIT')
            print('Migration successful!')
        except Exception as e:
            cursor.execute('ROLLBACK')
            print('Error during migration:', e)
            raise e
        finally:
            cursor.execute('PRAGMA foreign_keys = ON')
    else:
        print('Table already migrated.')
    conn.close()

if __name__ == '__main__':
    main()
