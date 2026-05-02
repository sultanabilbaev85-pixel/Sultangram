import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ime-ultra-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ime_pro.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Таблица пользователей
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(200), default='default.png')

# Таблица сообщений (с поддержкой фото)
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    image_path = db.Column(db.String(200)) # Путь к фото
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    channel = db.Column(db.String(100), default='general')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    msgs = Message.query.all() # Загружаем все сообщения из базы
    return render_template('index.html', user=current_user, messages=msgs)

@app.route('/send', methods=['POST'])
@login_required
def send():
    text = request.form.get('text')
    file = request.files.get('photo')
    filename = None
    
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    new_msg = Message(content=text, image_path=filename, user_id=current_user.id)
    db.session.add(new_msg)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hash_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(username=request.form.get('username'), password=hash_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
