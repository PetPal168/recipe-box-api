import os
from datetime import timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request, g
import sqlite3
from security import hash_password, verify_password
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, JWTManager

app = Flask(__name__)

load_dotenv()
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'fallback-secret-key')
jwt = JWTManager(app)

@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error": "token_expired",
        "message": "Token has expired, please log in again."
    }), 401

DATABASE = 'recipe_box.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- CUSTOM DECORATOR ---
def owner_or_admin_required(f):
    @wraps(f)
    def decorated_function(recipe_id, *args, **kwargs):
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get("role", "user")

        db = get_db()
        recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()

        if not recipe:
            db.close()
            return jsonify({"error": "Recipe not found"}), 404

        if user_role != "admin" and recipe['owner_id'] is not None and str(recipe['owner_id']) != str(user_id):
            db.close()
            return jsonify({"error": "Forbidden: You do not own this recipe"}), 403

        # Attach recipe to g so the route can use it
        g.recipe = recipe
        return f(recipe_id, *args, **kwargs)

    return decorated_function

# --- RECIPE ROUTES ---
@app.route('/recipes', methods=['GET'])
def get_recipes():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes').fetchall()
    db.close()
    return jsonify([dict(recipe) for recipe in recipes]), 200

@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    user_id = get_jwt_identity()
    data = request.get_json()
    title = data.get('title')
    instructions = data.get('instructions')
    
    if not title or not instructions:
        return jsonify({"error": "Missing title or instructions"}), 400
        
    db = get_db()
    db.execute('INSERT INTO recipes (title, instructions, owner_id) VALUES (?, ?, ?)', 
               (title, instructions, user_id))
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
@jwt_required()
@owner_or_admin_required
def update_recipe(recipe_id):
    data = request.get_json() or {}
    title = data.get('title')
    instructions = data.get('instructions')

    db = get_db()
    db.execute(
        'UPDATE recipes SET title = ?, instructions = ? WHERE id = ?',
        (title, instructions, recipe_id)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Recipe updated successfully"}), 200

@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@jwt_required()
@owner_or_admin_required
def delete_recipe(recipe_id):
    db = get_db()
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
        db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                   (username, email, hashed_pw))
        db.commit()
        return jsonify({
            "message": "User registered successfully",
            "user": {"username": username, "email": email}
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
    user = db.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,)).fetchone()
    db.close()

    if user is None or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"]}
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)