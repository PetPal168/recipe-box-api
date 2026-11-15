import sqlite3

# Connect to the database
conn = sqlite3.connect('recipe_box.db')
cursor = conn.cursor()

# Create the recipes table WITH owner_id
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        instructions TEXT NOT NULL,
        owner_id INTEGER
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

# Safely add owner_id to an existing recipes table if it's missing
try:
    cursor.execute("ALTER TABLE recipes ADD COLUMN owner_id INTEGER")
    print("Added 'owner_id' column to existing recipes table.")
except sqlite3.OperationalError:
    # This error means the column already exists, which is fine!
    pass

conn.commit()
conn.close()
print("Database updated: recipes and users tables ready!")