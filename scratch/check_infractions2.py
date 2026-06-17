import sqlite3

for db_path in ['database/cronograma.db', 'cronograma_inteligente.db', 'cronograma.db']:
    try:
        conn = sqlite3.connect(db_path)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if tables:
            print(f"\n=== {db_path} ===")
            infra_tables = [t for t in tables if 'infra' in t.lower()]
            if infra_tables:
                for t in infra_tables:
                    print(f"\nTabla: {t}")
                    rows = conn.execute(f"SELECT codigo_regla, count(*) FROM {t} WHERE cronograma_id=334 GROUP BY codigo_regla ORDER BY count(*) DESC").fetchall()
                    for r in rows:
                        print(f"  {r[0]}: {r[1]}")
            else:
                print("  No infra tables. Tables:", tables[:10])
        conn.close()
    except Exception as e:
        pass
