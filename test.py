import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
""")

cursor.execute("INSERT INTO users (name) VALUES ('Mathis')")
conn.commit()

cursor.execute("SELECT * FROM users")
print(cursor.fetchall())

conn.close()
