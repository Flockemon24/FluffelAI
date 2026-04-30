from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import requests
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from functools import wraps


load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

db_url = os.getenv("DATABASE_URL")

if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True  # nur HTTPS
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # wohin bei nicht eingeloggt



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=True)
    content = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))

class Accounts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    pass_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")


# --- AI --- #
def ask_ai(user_prompt):
    
    history = Message.query.filter_by(user_id=current_user.id).order_by(Message.created_at.desc()).limit(5).all()
    messages = [{"role": "system", "content": "Du bist FluffelAI, ein hilfreicher Assistenz-Bot. Antworte kurz, verständlich und logisch. Wenn etwas unklar ist, frag nach!"}]

    for msg in reversed(history):
        role = "assistant" if msg.user == "FluffelAI" else "user"
        messages.append({"role": role, "content": msg.content})

    messages.append({"role": "user", "content": user_prompt})
    # First API call with reasoning
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "openai/gpt-oss-120b:free",
            "messages": messages,
            "reasoning": {"enabled": True}
        })
    )
    

    try:
        # Extract the assistant message with reasoning_details
        response = response.json()
        print("ChatGPT")
        return response['choices'][0]['message']['content']
    
    except Exception as e:
        '''print("Fehler: ", e)
        print(response)
        return "Fehler"'''
        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "qwen/qwen3-next-80b-a3b-instruct:free",
            "messages": messages
            #"reasoning": {"enabled": True}
        })
        )

        try:
            # Extract the assistant message with reasoning_details
            response = response.json()
            print("Qwen")
            return response['choices'][0]['message']['content']
        
        except Exception as e:
            print("Fehler (Qwen): ", e)
            print(response)
            return "Fehler"
    


@login_manager.user_loader
def load_user(user_id):
    return Accounts.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Forbidden", 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/", methods=['GET', 'POST'])
def home_page():
    return render_template('homepage.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 🔍 Datenbank check
        existing_username = Accounts.query.filter_by(username=username).first()
        existing_email = Accounts.query.filter_by(email=email).first()

        if existing_username:
            return "Dieser Benutzername ist bereits vergeben!", 400
        
        if existing_email:
            return "Diese E-Mail ist bereits registriert! Bitte versuche dich anzumelden.", 400

        # 👤 neuen User erstellen
        new_user = Accounts(
            username=username,
            email=email,
            pass_hash=generate_password_hash(password)
        )
        

        db.session.add(new_user)
        db.session.commit()

        # 🔐 Login direkt nach Registrierung
        login_user(new_user)

        return redirect(url_for('start_page'))

    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        login_value = request.form.get("login")
        password = request.form.get("password")

        user = Accounts.query.filter(
            (Accounts.username == login_value) | (Accounts.email == login_value)
        ).first()

        if not user or not check_password_hash(user.pass_hash, password):
            return "Login fehlgeschlagen", 400

        login_user(user)  # 🔥 DAS ist der Unterschied!
        return redirect(url_for("start_page"))

    return render_template("login.html")

@app.route("/chat", methods=['GET', 'POST'])
@login_required
def start_page():
    if request.method == 'POST':
        new_message = Message(
            user = current_user.username,
            content = request.form['content'],
            user_id = current_user.id
        )
        db.session.add(new_message)
        db.session.commit()

        new_answer = Message(
            user = "FluffelAI",
            content = ask_ai(request.form['content']),
            user_id = current_user.id
        )
        db.session.add(new_answer)
        db.session.commit()

    messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.created_at).all()
    return render_template('index.html', messages=messages, name=current_user.username)

@app.route("/profile")
@login_required
def profile():
    return f"Hallo {current_user.username}"

@app.route("/clear", methods=['POST']) # Nur POST erlauben
@login_required
@admin_required
def clear_messages():
    try:
        db.session.query(Message).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Fehler: {e}")
    
    # Leitet den Nutzer nach dem Löschen sofort zurück zur Startseite
    return redirect(url_for('start_page', name='user')) 

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()