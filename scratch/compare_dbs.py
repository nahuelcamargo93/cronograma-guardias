import sqlite3
import json

def compare():
    db_git = sqlite3.connect("scratch/git_db.db")
    db_user = sqlite3.connect("scratch/temp_db.db")
    
    def get_all_rows(db, table_name):
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        return cur.fetchall()
        
    git_pra = get_all_rows(db_git, "personal_reglas_ajustes")
    user_pra = get_all_rows(db_user, "personal_reglas_ajustes")
    
    # Compare by all elements except ID if IDs can differ
    print("=== Comparing personal_reglas_ajustes ===")
    git_set = {r[1:]: r for r in git_pra}
    user_set = {r[1:]: r for r in user_pra}
    
    only_in_git = git_set.keys() - user_set.keys()
    only_in_user = user_set.keys() - git_set.keys()
    
    if only_in_git:
        print("Only in Git database:")
        for k in only_in_git:
            print(f"  {git_set[k]}")
            
    if only_in_user:
        print("Only in User database:")
        for k in only_in_user:
            print(f"  {user_set[k]}")
            
    if not only_in_git and not only_in_user:
        print("No differences in personal_reglas_ajustes!")
        
    db_git.close()
    db_user.close()

if __name__ == '__main__':
    compare()
