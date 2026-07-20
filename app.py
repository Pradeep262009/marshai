import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import save_chat_history, get_user_chat_history, get_total_chats
from agent import ask_marshai
from datetime import datetime
from dotenv import load_dotenv
import os
import pyrebase

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ── Firebase Config ──────────────────────────────────
firebaseConfig = {
    "apiKey":             os.getenv('FIREBASE_API_KEY'),
    "authDomain":         os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId":          os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket":      os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId":  os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId":              os.getenv('FIREBASE_APP_ID'),
    "measurementId":      os.getenv('FIREBASE_MEASUREMENT_ID'),
    "databaseURL":        os.getenv('FIREBASE_DATABASE_URL', "")
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth     = firebase.auth()

# ── Flask Config ─────────────────────────────────────
app = Flask(__name__, static_folder='templates/static')
app.secret_key = os.getenv('SECRET_KEY', 'marshai-firebase-secret-2024')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
)

# ── Helper ────────────────────────────────────────────
def get_current_user():
    return session.get('user')

# ── Routes ────────────────────────────────────────────

@app.route('/')
def index():
    if get_current_user():
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# ── Signup ────────────────────────────────────────────
@app.route('/signup', methods=['POST'])
def signup():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not name or not email or '@' not in email or len(password) < 6:
        error = 'Enter a valid name, email, and password of at least 6 characters.'
        return render_template('index.html', error=error)

    try:
        # Firebase creates the user
        user = auth.create_user_with_email_and_password(email, password)
        session['user'] = {
            'uid':   user['localId'],
            'email': email,
            'name':  name
        }
        return redirect(url_for('dashboard'))
    except Exception as e:
        error = "Signup failed! Email may already exist or password is invalid."
        return render_template('index.html', error=error)

# ── Login ─────────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not email or '@' not in email or len(password) < 6:
        error = 'Enter a valid email and password of at least 6 characters.'
        return render_template('index.html', error=error)

    try:
        # Firebase verifies credentials
        user = auth.sign_in_with_email_and_password(email, password)
        session['user'] = {
            'uid':   user['localId'],
            'email': email,
            'name':  email.split('@')[0].capitalize()
        }
        return redirect(url_for('dashboard'))
    except Exception as e:
        error = "Login failed! Check your email and password."
        return render_template('index.html', error=error)

# ── Logout ────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# ── Password Reset ────────────────────────────────────
@app.route('/reset', methods=['POST'])
def reset():
    email = request.form.get('email')
    try:
        auth.send_password_reset_email(email)
        return render_template('index.html',
               success="✅ Password reset email sent! Check your inbox.")
    except:
        return render_template('index.html',
               error="❌ Email not found.")

# ── Dashboard ─────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    total_chats = get_total_chats(firebase, user['uid'])
    return render_template('dashboard.html',
                           user=user,
                           total_chats=total_chats)

# ── Chat ──────────────────────────────────────────────
@app.route('/chat')
def chat():
    if not get_current_user():
        return redirect(url_for('index'))
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    user = get_current_user()
    if not user:
        return jsonify({'answer': '⚠️ Please login first.'})
    data       = request.get_json()
    question   = data.get('question', '')
    image_data = data.get('image', None) # dict {mime_type, data}
    answer     = ask_marshai(question, image_data)
    
    # Save to Firebase (indicate image attachment in database log)
    db_question = f"📷 [Image Scan] {question}" if image_data else question
    save_chat_history(firebase, user['uid'], user['email'], db_question, answer)
    
    return jsonify({'answer': answer})

# ── History ───────────────────────────────────────────
@app.route('/history')
def history():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    chats = get_user_chat_history(firebase, user['uid'])
    return render_template('history.html', chats=chats)

# ── Account ───────────────────────────────────────────
@app.route('/account')
def account():
    user = get_current_user()
    if not user:
        return redirect(url_for('index'))
    total = get_total_chats(firebase, user['uid'])
    return render_template('account.html', user=user, total=total)

# ── About ─────────────────────────────────────────────
@app.route('/about')
def about():
    return render_template('about.html')

# ── Run ───────────────────────────────────────────────
if __name__ == '__main__':

    app.run(debug=True)