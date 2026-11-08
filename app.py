from flask import Flask, jsonify, request
import sqlite3
from security import hash_password, verify_password

app = Flask(__name__)
DATABASE = 'recipe_box.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return jsonify({"message": "Recipe Box API is running!"})

# --- RECIPE ROUTES ---
@app.route('/recipes', methods=['GET'])
def get_recipes():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes').fetchall()
    db.close()
    return jsonify([dict(recipe) for recipe in recipes]), 200

@app.route('/recipes', methods=['POST'])
def create_recipe():
    data = request.get_json()
    title = data.get('title')
    instructions = data.get('instructions')
    if not title or not instructions:
        return jsonify({"error": "Missing title or instructions"}), 400
    db = get_db()
    db.execute('INSERT INTO recipes (title, instructions) VALUES (?, ?)', (title, instructions))
    db.commit()
    db.close()
    return jsonify({"message": "Recipe added successfully!"}), 201

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_single_recipe(recipe_id):
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    db.close()
    if recipe:
        return jsonify(dict(recipe)), 200
    return jsonify({"error": "Recipe not found"}), 404

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
    db.execute('UPDATE recipes SET title = ?, instructions = ? WHERE id = ?', (title, instructions, recipe_id))
    db.commit()
    db.close()
    return jsonify({"message": "Recipe updated successfully"}), 200

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

# --- AUTHENTICATION ROUTES ---
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "Missing or blank username, email, or password"}), 400

    hashed_pw = hash_password(password)
    db = get_db()
    
    try:
        db.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, hashed_pw)
        )
        db.commit()
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "username": username,
                "email": email
            }
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already taken"}), 409
    finally:
        db.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    user = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    # Generic failure: unknown user OR wrong password -> same response
    if user is None or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Success: return identity, but never the password/hash
    return jsonify({
        "id": user["id"],
        "username": user["username"]
    }), 200

# --- DEBUG ROUTE ---
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