import sqlite3
import os

src_db = "cronograma_inteligente.db"
dst_db = "cronograma_inteligente_recovered.db"

if os.path.exists(dst_db):
    os.remove(dst_db)

print(f"Attempting to recover data from '{src_db}' to '{dst_db}'...")

try:
    conn_src = sqlite3.connect(src_db)
    conn_dst = sqlite3.connect(dst_db)
    
    # 1. Get all table names and their schema
    tables = conn_src.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    
    for name, sql in tables:
        print(f"\nProcessing table: {name}")
        # Create table in destination
        try:
            conn_dst.execute(sql)
            print(f"  Table structure created.")
        except Exception as e:
            print(f"  Error creating table structure: {e}")
            continue
            
        # Select and insert data row by row to catch corruption
        try:
            cursor_src = conn_src.execute(f"SELECT * FROM [{name}]")
            # Get columns to build insert statement
            columns = [col[0] for col in cursor_src.description]
            placeholders = ",".join("?" for _ in columns)
            insert_sql = f"INSERT INTO [{name}] ({','.join(f'[{c}]' for c in columns)}) VALUES ({placeholders})"
            
            row_count = 0
            while True:
                try:
                    row = cursor_src.fetchone()
                    if row is None:
                        break
                    conn_dst.execute(insert_sql, row)
                    row_count += 1
                except sqlite3.DatabaseError as de:
                    print(f"  [ERROR] Database corruption hit in table '{name}' at row {row_count}: {de}")
                    break
                except Exception as e:
                    print(f"  [ERROR] General error at row {row_count}: {e}")
                    break
            
            conn_dst.commit()
            print(f"  Successfully recovered {row_count} rows.")
        except Exception as e:
            print(f"  Failed to query table '{name}': {e}")
            
    # Copy indexes and triggers
    other_objects = conn_src.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE type IN ('index', 'trigger', 'view') AND sql IS NOT NULL"
    ).fetchall()
    
    for obj_type, obj_name, sql in other_objects:
        try:
            conn_dst.execute(sql)
            print(f"Created {obj_type}: {obj_name}")
        except Exception as e:
            print(f"Error creating {obj_type} '{obj_name}': {e}")
            
    conn_dst.commit()
    conn_src.close()
    conn_dst.close()
    print("\nRecovery process finished.")
    
except Exception as e:
    print("General recovery failure:", e)
