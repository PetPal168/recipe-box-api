from flask import Flask, jsonify, request
import sqlite3

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

if __name__ == '__main__':
    app.run(port=5000, debug=True)