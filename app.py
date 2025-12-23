from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash   # DITAMBAHKAN
app = Flask(__name__)
app.secret_key = 'secret123'   # DITAMBAHKAN untuk mengaktifkan session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from flask_wtf import CSRFProtect  # DITAMBAHKAN
csrf = CSRFProtect(app)            # DITAMBAHKAN


class User(db.Model):                # DITAMBAHKAN
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Password sudah di-hash

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    
    def __repr__(self):
        return f'<Student {self.name}>'

@app.route('/init-admin')
def init_admin():
    """Route untuk inisialisasi admin user (gunakan sekali saja)"""
    hashed_pw = generate_password_hash('admin')
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        return "Admin user sudah ada"
    new_user = User(username='admin', password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return "Admin user berhasil dibuat. Username: admin, Password: admin"

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username sudah terdaftar')

        # Check if passwords match
        if password != confirm_password:
            return render_template('register.html', error='Password tidak cocok')

        # Check password length
        if len(password) < 3:
            return render_template('register.html', error='Password minimal 3 karakter')

        # Create new user
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/')
def index():
    # RAW Query
    # SEBELUM:
    # students = db.session.execute(text('SELECT * FROM student')).fetchall()

    if 'logged_in' not in session:          # DITAMBAHKAN
        return redirect(url_for('login'))

    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()     # DITAMBAHKAN
        if user and check_password_hash(user.password, password):  # DITAMBAHKAN
            session['logged_in'] = True
            return redirect(url_for('index'))
        return "Invalid username or password"

    return render_template('login.html')

@app.route('/add', methods=['POST'])
def add_student():
    if 'logged_in' not in session:                 # DITAMBAHKAN
         return redirect(url_for('login'))
    
    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']
    
    connection = sqlite3.connect('instance/students.db')
    cursor = connection.cursor()

    # RAW Query
    # db.session.execute(
    #     text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
    #     {'name': name, 'age': age, 'grade': grade}
    # )
    # db.session.commit()
    # Sebelum:
    #query = f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    #cursor.execute(query)

    db.session.execute(                         # DITAMBAHKAN
     text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
     {'name': name, 'age': age, 'grade': grade}
 )
    db.session.commit()
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST']) # DIUBAH: GET -> POST
 
def delete_student(id):
    if 'logged_in' not in session:                 # DITAMBAHKAN
        return redirect(url_for('login'))
    # RAW Query
    # SEBELUM:
    # db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.execute(text("DELETE FROM student WHERE id=:id"), {'id': id})  # DITAMBAHKAN
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'logged_in' not in session:                    # DITAMBAHKAN
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']
        
        # RAW Query
        # SEBELUM:
        # db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        db.session.execute(
            text("UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id"),  
            {'name': name, 'age': age, 'grade': grade, 'id': id}
        )
        db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query
        student = db.session.execute(text(f"SELECT * FROM student WHERE id={id}")).fetchone()
        return render_template('edit.html', student=student)
    
@app.route('/logout')
def logout():
    session.pop('logged_in', None)            # DITAMBAHKAN
    return redirect(url_for('login'))


# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

