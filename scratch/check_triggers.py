import database.connection as c
conn = c.get_connection()
print(conn.execute("select name from sqlite_master where type='trigger'").fetchall())
