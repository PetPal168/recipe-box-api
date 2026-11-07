from flask import Flask, jsonify, request
import sqlite3
from security import hash_password, verify_password

app = Flask(__name__)
DATABASE = 'recipe_box.db'

# Helper function to connect to the database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return jsonify({"message": "Recipe Box API is running!"})

# GET all recipes
@app.route('/recipes', methods=['GET'])
def get_recipes():
    db = get_db()
    try:
        recipes = db.execute('SELECT * FROM recipes').fetchall()
        db.close()
        return jsonify([dict(recipe) for recipe in recipes]), 200
    except sqlite3.OperationalError:
        db.close()
        return jsonify([]), 200

# POST a new recipe
@app.route('/recipes', methods=['POST'])
def create_recipe():
    data = request.get_json()
    title = data.get('title')
    instructions = data.get('instructions')
    
    if not title or not instructions:
        return jsonify({"error": "Missing title or instructions"}), 400
        
    db = get_db()
    try:
        db.execute('INSERT INTO recipes (title, instructions) VALUES (?, ?)', (title, instructions))
        db.commit()
        db.close()
        return jsonify({"message": "Recipe added successfully!"}), 201
    except sqlite3.OperationalError as e:
        db.close()
        return jsonify({"error": f"Database error: {e}"}), 500

# GET a single recipe by ID
@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_single_recipe(recipe_id):
    db = get_db()
    try:
        recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
        db.close()
        
        if recipe:
            return jsonify(dict(recipe)), 200
        else:
            return jsonify({"error": "Recipe not found"}), 404
            
    except sqlite3.OperationalError:
        db.close()
        return jsonify({"error": "Table not found. Did you run init_db.py?"}), 500

# PUT (Update) a recipe by ID - The vulnerability
@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    data = request.get_json()
    title = data.get('title')
    instructions = data.get('instructions')
    
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    
    if not recipe:
        db.close()
        return jsonify({"error": "Recipe not found"}), 404
        
    db.execute('UPDATE recipes SET title = ?, instructions = ? WHERE id = ?', 
               (title, instructions, recipe_id))
    db.commit()
    db.close()
    
    return jsonify({"message": "Recipe updated successfully"}), 200

# DELETE a recipe by ID - The vulnerability
@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    
    if not recipe:
        db.close()
        return jsonify({"error": "Recipe not found"}), 404
        
    db.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
    db.commit()
    db.close()
    
    return jsonify({"message": "Recipe deleted successfully"}), 200

# REGISTER a new user securely
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 1. Basic validation
    if not username or not email or not password:
        return jsonify({"error": "Missing username, email, or password"}), 400

    # 2. Hash the password securely using our new security.py file
    hashed_password = hash_password(password)

    db = get_db()
    try:
        # 3. Insert the user with the HASH, not the real password
        db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', 
                   (username, email, hashed_password))
        db.commit()
        db.close()
        return jsonify({"message": f"User {username} registered securely!"}), 201
        
    except sqlite3.IntegrityError:
        # Catches UNIQUE constraint error for duplicate username/email
        db.close()
        return jsonify({"error": "Username or email already taken"}), 409

# --- DEBUG ROUTE FOR TESTING HASHING ---
@app.route("/debug/password-test")
def password_test():
    password = "TestPassword123!"
    stored_hash = hash_password(password)

    correct = verify_password(stored_hash, "TestPassword123!")
    wrong = verify_password(stored_hash, "WrongPassword")

    return {
        "password": "not returned",
        "stored_hash": stored_hash,
        "correct_candidate_result": correct,
        "wrong_candidate_result": wrong,
    }

if __name__ == '__main__':
    app.run(port=5000, debug=True)