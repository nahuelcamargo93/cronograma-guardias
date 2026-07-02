import database.connection as c
conn = c.get_connection()
tables = conn.execute("select name from sqlite_master where type='table'").fetchall()
for t in sorted(tables):
    print(t[0])
