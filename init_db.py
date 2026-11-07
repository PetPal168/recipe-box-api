import sqlite3

# Connect to the database
conn = sqlite3.connect('recipe_box.db')
cursor = conn.cursor()

# Create the recipes table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        instructions TEXT NOT NULL
    )
''')

# Create the users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
print("Database updated: recipes and users tables created successfully!")