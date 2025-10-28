from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from datetime import datetime, timedelta
import os
import json
from ocr_model import ExpiryDateExtractor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your MySQL password
    'database': 'food_expiry_tracker'
}

# Email configuration (optional)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'your_email@gmail.com',
    'password': 'your_app_password'
}

# Initialize OCR extractor
ocr_extractor = ExpiryDateExtractor()

def get_db_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def update_food_status():
    """Update food item status based on expiry date"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    today = datetime.now().date()
    near_expiry_date = today + timedelta(days=3)
    
    # Update statuses
    cursor.execute("""
        UPDATE food_items 
        SET status = CASE
            WHEN expiry_date < %s THEN 'Expired'
            WHEN expiry_date BETWEEN %s AND %s THEN 'Near Expiry'
            ELSE 'Fresh'
        END
    """, (today, today, near_expiry_date))
    
    conn.commit()
    cursor.close()
    conn.close()

def send_email_notification(user_email, food_name, expiry_date):
    """Send email notification for near expiry items"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = user_email
        msg['Subject'] = f'Food Expiry Alert: {food_name}'
        
        body = f"""
        Hello,
        
        This is a reminder that your food item "{food_name}" is expiring soon.
        
        Expiry Date: {expiry_date}
        
        Please consume or use it before it expires to avoid food waste.
        
        Best regards,
        Food Expiry Tracker
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email notification error: {e}")
        return False

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
        
        return suggestions[:5]  # Return top 5 suggestions
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
        if not conn:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        cursor.close()
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
        if not conn:
            flash('Database connection error', 'error')
            return render_template('signup.html')
        
        cursor = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                         (username, email, password_hash))
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        except mysql.connector.Error as e:
            flash('Username or email already exists', 'error')
            cursor.close()
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
    if not conn:
        flash('Database connection error', 'error')
        return render_template('index.html', food_items=[])
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT id, food_name, expiry_date, purchase_date, status, category, quantity, 
               DATEDIFF(expiry_date, CURDATE()) as days_remaining
        FROM food_items 
        WHERE user_id = %s 
        ORDER BY expiry_date ASC
    ''', (session['user_id'],))
    
    food_items = cursor.fetchall()
    cursor.close()
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
            # Extract expiry date using OCR
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
    purchase_date = request.form.get('purchase_date', datetime.now().date())
    category = request.form.get('category', 'Other')
    quantity = request.form.get('quantity', '')
    notes = request.form.get('notes', '')
    image_path = request.form.get('image_path', '')
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO food_items 
            (user_id, food_name, expiry_date, purchase_date, category, quantity, notes, image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (session['user_id'], food_name, expiry_date, purchase_date, category, quantity, notes, image_path))
        
        conn.commit()
        flash('Food item added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error adding food item: {str(e)}', 'error')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    """Delete food item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})
    
    cursor = conn.cursor()
    cursor.execute('DELETE FROM food_items WHERE id = %s AND user_id = %s', 
                  (food_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Food item deleted'})

@app.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    update_food_status()
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('dashboard.html')
    
    cursor = conn.cursor(dictionary=True)
    
    # Get statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN status = 'Fresh' THEN 1 ELSE 0 END) as fresh_count,
            SUM(CASE WHEN status = 'Near Expiry' THEN 1 ELSE 0 END) as near_expiry_count,
            SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) as expired_count
        FROM food_items 
        WHERE user_id = %s
    ''', (session['user_id'],))
    
    stats = cursor.fetchone()
    
    # Get near expiry items
    cursor.execute('''
        SELECT food_name, expiry_date, DATEDIFF(expiry_date, CURDATE()) as days_remaining
        FROM food_items 
        WHERE user_id = %s AND status = 'Near Expiry'
        ORDER BY expiry_date ASC
    ''', (session['user_id'],))
    
    near_expiry_items = cursor.fetchall()
    
    # Get category breakdown
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM food_items 
        WHERE user_id = %s
        GROUP BY category
    ''', (session['user_id'],))
    
    category_data = cursor.fetchall()
    
    # Get monthly trend (last 6 months)
    cursor.execute('''
        SELECT 
            DATE_FORMAT(expiry_date, '%Y-%m') as month,
            COUNT(*) as expired_count
        FROM food_items 
        WHERE user_id = %s AND expiry_date < CURDATE()
        AND expiry_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY month
        ORDER BY month
    ''', (session['user_id'],))
    
    monthly_trend = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Get recipe suggestions
    recipes = get_recipe_suggestions(near_expiry_items)
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         near_expiry_items=near_expiry_items,
                         category_data=category_data,
                         monthly_trend=monthly_trend,
                         recipes=recipes)

@app.route('/api/check_notifications')
def check_notifications():
    """Check and send notifications for near expiry items"""
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False})
    
    cursor = conn.cursor(dictionary=True)
    
    today = datetime.now().date()
    notification_date = today + timedelta(days=3)
    
    cursor.execute('''
        SELECT id, food_name, expiry_date
        FROM food_items 
        WHERE user_id = %s 
        AND status = 'Near Expiry'
        AND expiry_date <= %s
    ''', (session['user_id'], notification_date))
    
    items = cursor.fetchall()
    notifications = []
    
    for item in items:
        days_left = (item['expiry_date'] - today).days
        message = f"{item['food_name']} will expire in {days_left} days"
        notifications.append(message)
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'notifications': notifications})

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
