from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, timedelta
import os
import json
from ocr_model import ExpiryDateExtractor
from ai_assistant_gemini import FoodAIAssistant  # Using Gemini (FREE)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here_change_in_production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# SQLite Database
DATABASE = 'food_tracker.db'

# Initialize OCR extractor and AI assistant
ocr_extractor = ExpiryDateExtractor()
ai_assistant = FoodAIAssistant()

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Food items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            expiry_date DATE NOT NULL,
            purchase_date DATE DEFAULT (date('now')),
            image_path TEXT,
            status TEXT DEFAULT 'Fresh',
            category TEXT,
            quantity TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # Insert default categories
    categories = [
        ('Dairy', 'Milk, cheese, yogurt, butter'),
        ('Vegetables', 'Fresh vegetables'),
        ('Fruits', 'Fresh fruits'),
        ('Meat & Poultry', 'Chicken, beef, pork, lamb'),
        ('Seafood', 'Fish and shellfish'),
        ('Beverages', 'Drinks and juices'),
        ('Bakery', 'Bread, pastries, cakes'),
        ('Frozen Foods', 'Frozen meals and items'),
        ('Canned Goods', 'Canned vegetables, fruits, soups'),
        ('Condiments', 'Sauces, dressings, spices'),
        ('Snacks', 'Chips, cookies, crackers'),
        ('Other', 'Miscellaneous items')
    ]
    
    for cat in categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', cat)
    
    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def update_food_status():
    """Update food item status based on expiry date"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    near_expiry_date = today + timedelta(days=3)
    
    cursor.execute('''
        UPDATE food_items 
        SET status = CASE
            WHEN expiry_date < date('now') THEN 'Expired'
            WHEN expiry_date BETWEEN date('now') AND date('now', '+3 days') THEN 'Near Expiry'
            ELSE 'Fresh'
        END
    ''')
    
    conn.commit()
    conn.close()

def get_recipe_suggestions(food_items):
    """Get recipe suggestions based on near expiry items"""
    try:
        with open('recipes.json', 'r') as f:
            recipes = json.load(f)
        
        suggestions = []
        for food in food_items:
            food_name_lower = food['food_name'].lower()
            for recipe in recipes:
                ingredients_lower = [ing.lower() for ing in recipe['ingredients']]
                if any(food_name_lower in ing or ing in food_name_lower for ing in ingredients_lower):
                    if recipe not in suggestions:
                        suggestions.append(recipe)
        
        return suggestions[:5]
    except Exception as e:
        print(f"Recipe suggestion error: {e}")
        return []

# Routes

@app.route('/')
def home():
    """Home page - redirect to login or index"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        conn = get_db_connection()
        
        try:
            password_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
            conn.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/index')
def index():
    """Main dashboard - upload and list food items"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    update_food_status()
    
    conn = get_db_connection()
    food_items = conn.execute('''
        SELECT id, food_name, expiry_date, purchase_date, status, category, quantity,
               julianday(expiry_date) - julianday('now') as days_remaining
        FROM food_items 
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('index.html', food_items=food_items)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and OCR processing"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            expiry_date, extracted_text = ocr_extractor.extract_expiry_date(filepath)
            food_name = ocr_extractor.extract_food_name(extracted_text)
            
            if expiry_date:
                return jsonify({
                    'success': True,
                    'expiry_date': expiry_date,
                    'food_name': food_name,
                    'image_path': filename,
                    'message': 'Expiry date extracted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'food_name': food_name,
                    'image_path': filename,
                    'message': 'Could not extract expiry date. Please enter manually.',
                    'extracted_text': extracted_text
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'OCR processing error: {str(e)}',
                'image_path': filename
            })
    
    return jsonify({'success': False, 'message': 'Invalid file format'})

@app.route('/add_food', methods=['POST'])
def add_food():
    """Add food item to database"""
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    food_name = request.form.get('food_name')
    expiry_date = request.form.get('expiry_date')
    purchase_date = request.form.get('purchase_date') or datetime.now().date()
    category = request.form.get('category', 'Other')
    quantity = request.form.get('quantity', '')
    notes = request.form.get('notes', '')
    image_path = request.form.get('image_path', '')
    
    conn = get_db_connection()
    
    try:
        conn.execute('''
            INSERT INTO food_items 
            (user_id, food_name, expiry_date, purchase_date, category, quantity, notes, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], food_name, expiry_date, purchase_date, category, quantity, notes, image_path))
        
        conn.commit()
        flash('Food item added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding food item: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    """Delete food item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    conn = get_db_connection()
    conn.execute('DELETE FROM food_items WHERE id = ? AND user_id = ?', 
                (food_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Food item deleted'})

@app.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    update_food_status()
    
    conn = get_db_connection()
    
    # Get statistics
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN status = 'Fresh' THEN 1 ELSE 0 END) as fresh_count,
            SUM(CASE WHEN status = 'Near Expiry' THEN 1 ELSE 0 END) as near_expiry_count,
            SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) as expired_count
        FROM food_items 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    # Get near expiry items
    near_expiry_items = conn.execute('''
        SELECT food_name, expiry_date, 
               julianday(expiry_date) - julianday('now') as days_remaining
        FROM food_items 
        WHERE user_id = ? AND status = 'Near Expiry'
        ORDER BY expiry_date ASC
    ''', (session['user_id'],)).fetchall()
    
    # Get category breakdown
    category_data_rows = conn.execute('''
        SELECT category, COUNT(*) as count
        FROM food_items 
        WHERE user_id = ?
        GROUP BY category
    ''', (session['user_id'],)).fetchall()
    
    # Get monthly trend
    monthly_trend_rows = conn.execute('''
        SELECT 
            strftime('%Y-%m', expiry_date) as month,
            COUNT(*) as expired_count
        FROM food_items 
        WHERE user_id = ? AND expiry_date < date('now')
        AND expiry_date >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Convert Row objects to dictionaries for JSON serialization
    category_data = [dict(row) for row in category_data_rows]
    monthly_trend = [dict(row) for row in monthly_trend_rows]
    near_expiry_items = [dict(row) for row in near_expiry_items]
    
    # Check if AI recipes are cached (don't auto-generate)
    ai_recipes = []
    if near_expiry_items and len(near_expiry_items) > 0:
        ingredients = [item['food_name'] for item in near_expiry_items[:5]]
        cache_key = f"recipes_{session['user_id']}_{'_'.join(sorted(ingredients))}"
        
        # Only load from cache, don't generate automatically
        if cache_key in session and session.get(cache_key):
            ai_recipes = session[cache_key]
            print("Using cached recipes")
    
    # Get fallback recipes from JSON
    fallback_recipes = get_recipe_suggestions(near_expiry_items) if not ai_recipes else []
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         near_expiry_items=near_expiry_items,
                         category_data=category_data,
                         monthly_trend=monthly_trend,
                         ai_recipes=ai_recipes,
                         fallback_recipes=fallback_recipes)

@app.route('/api/check_notifications')
def check_notifications():
    """Check and send notifications for near expiry items"""
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    conn = get_db_connection()
    
    items = conn.execute('''
        SELECT id, food_name, expiry_date
        FROM food_items 
        WHERE user_id = ? 
        AND status = 'Near Expiry'
        AND expiry_date <= date('now', '+3 days')
    ''', (session['user_id'],)).fetchall()
    
    notifications = []
    for item in items:
        days_left = (datetime.strptime(item['expiry_date'], '%Y-%m-%d').date() - datetime.now().date()).days
        message = f"{item['food_name']} will expire in {days_left} days"
        notifications.append(message)
    
    conn.close()
    
    return jsonify({'success': True, 'notifications': notifications})

# ============ AI ASSISTANT ROUTES ============

@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'success': False, 'message': 'No message provided'})
    
    # Get user's food context
    conn = get_db_connection()
    food_items = conn.execute('''
        SELECT food_name, expiry_date, status
        FROM food_items 
        WHERE user_id = ?
        ORDER BY expiry_date ASC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    context = {
        'food_items': [dict(item) for item in food_items],
        'username': session.get('username')
    }
    
    # Get AI response
    result = ai_assistant.chat_with_assistant(user_message, context)
    
    return jsonify({
        'success': result['success'],
        'response': result['response']
    })

@app.route('/ai/generate-recipe', methods=['POST'])
def ai_generate_recipe():
    """Generate AI recipe from selected ingredients"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    ingredients = data.get('ingredients', [])
    dietary_prefs = data.get('dietary_preferences', None)
    
    if not ingredients:
        return jsonify({'success': False, 'message': 'No ingredients provided'})
    
    # Generate recipe
    recipe = ai_assistant.generate_recipe_from_ingredients(ingredients, dietary_prefs)
    
    return jsonify({
        'success': True,
        'recipe': recipe
    })

@app.route('/ai/storage-tip/<int:food_id>')
def ai_storage_tip(food_id):
    """Get AI storage advice for a food item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    conn = get_db_connection()
    food = conn.execute('''
        SELECT food_name FROM food_items 
        WHERE id = ? AND user_id = ?
    ''', (food_id, session['user_id'])).fetchone()
    conn.close()
    
    if not food:
        return jsonify({'success': False, 'message': 'Food item not found'})
    
    # Get storage advice
    advice = ai_assistant.get_food_storage_advice(food['food_name'])
    
    return jsonify({
        'success': advice['success'],
        'advice': advice['advice']
    })

@app.route('/ai/meal-plan')
def ai_meal_plan():
    """Generate weekly meal plan"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    conn = get_db_connection()
    items = conn.execute('''
        SELECT food_name, 
               julianday(expiry_date) - julianday('now') as days_left
        FROM food_items 
        WHERE user_id = ? AND status != 'Expired'
        ORDER BY expiry_date ASC
        LIMIT 15
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    available_items = [
        {'name': item['food_name'], 'days_left': int(item['days_left'])}
        for item in items
    ]
    
    # Generate meal plan
    result = ai_assistant.suggest_meals_for_week(available_items)
    
    return jsonify({
        'success': result['success'],
        'meal_plan': result['meal_plan']
    })

@app.route('/ai/quick-tip/<food_name>')
def ai_quick_tip(food_name):
    """Get quick tip for a food item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    tip = ai_assistant.get_quick_tip(food_name)
    
    return jsonify({
        'success': True,
        'tip': tip
    })

@app.route('/ai/generate-recipes', methods=['POST'])
def generate_recipes_endpoint():
    """Generate AI recipes on demand"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        # Get near expiry items
        conn = get_db_connection()
        near_expiry_items = conn.execute('''
            SELECT food_name, expiry_date
            FROM food_items 
            WHERE user_id = ? AND status = 'Near Expiry'
            ORDER BY expiry_date ASC
            LIMIT 5
        ''', (session['user_id'],)).fetchall()
        conn.close()
        
        if not near_expiry_items or len(near_expiry_items) == 0:
            return jsonify({
                'success': False,
                'message': 'No near-expiry items found. Add some food items first!'
            })
        
        # Get ingredients
        ingredients = [item['food_name'] for item in near_expiry_items]
        cache_key = f"recipes_{session['user_id']}_{'_'.join(sorted(ingredients))}"
        
        # Generate 2 AI recipes
        ai_recipes = []
        for i in range(2):
            dietary_pref = None if i == 0 else "quick and easy"
            ai_recipe = ai_assistant.generate_recipe_from_ingredients(ingredients, dietary_pref)
            if ai_recipe and ai_recipe.get('recipe_name'):
                ai_recipes.append(ai_recipe)
        
        # Cache recipes
        session[cache_key] = ai_recipes
        session.permanent = True
        
        return jsonify({
            'success': True,
            'recipes': ai_recipes,
            'count': len(ai_recipes)
        })
        
    except Exception as e:
        print(f"Error generating recipes: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/ai/regenerate-recipes', methods=['POST'])
def regenerate_recipes():
    """Clear recipe cache and regenerate"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    # Clear all recipe caches for this user
    keys_to_remove = [key for key in session.keys() if key.startswith(f'recipes_{session["user_id"]}_')]
    for key in keys_to_remove:
        session.pop(key, None)
    
    return jsonify({
        'success': True,
        'message': 'Cache cleared. Click Generate to create new recipes.'
    })

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
