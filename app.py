from flask_socketio import SocketIO
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

import pandas as pd
import numpy as np

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'

# CHANGE PASSWORD BELOW
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2039@localhost/taskmanager'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# ================= MODELS ================= #

class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


class Task(db.Model):

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(db.Text)

    priority = db.Column(db.String(50))

    status = db.Column(db.String(50))

    created_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id')
    )

# ================= HOME ================= #

@app.route('/')
def home():

    return redirect('/login')

# ================= REGISTER ================= #

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# ================= LOGIN ================= #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id

            session['username'] = user.username

            return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template('login.html')

# ================= DASHBOARD / GET ALL TASKS ================= #

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    # GET ALL TASKS
    tasks = Task.query.filter_by(
        user_id=session['user_id']
    ).all()

    # ANALYTICS
    task_data = []

    for task in tasks:

        task_data.append({
            'title': task.title,
            'status': task.status
        })

    df = pd.DataFrame(task_data)

    total_tasks = len(df)

    completed_tasks = len(
        df[df['status'] == 'Completed']
    ) if not df.empty else 0

    pending_tasks = len(
        df[df['status'] == 'Pending']
    ) if not df.empty else 0

    completion_percentage = np.round(
        (completed_tasks / total_tasks) * 100,
        2
    ) if total_tasks > 0 else 0

    return render_template(
        'dashboard.html',
        username=session['username'],
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completion_percentage=completion_percentage
    )
# ================= GET ALL TASKS PAGE ================= #

@app.route('/all_tasks')
def all_tasks():

    if 'user_id' not in session:
        return redirect('/login')

    tasks = Task.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'all_tasks.html',
        tasks=tasks,
        username=session['username']
    )
# ================= ADD TASK PAGE ================= #

@app.route('/add_task_page')
def add_task_page():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template('add_task.html')

# ================= ADD TASK ================= #

@app.route('/add_task', methods=['POST'])
def add_task():

    if 'user_id' not in session:
        return redirect('/login')

    new_task = Task(

        title=request.form['title'],

        description=request.form['description'],

        priority=request.form['priority'],

        status=request.form['status'],

        user_id=session['user_id']
    )

    db.session.add(new_task)

    socketio.emit(
        'new_task',
        {
            'message': 'New Task Added Successfully'
        }
    )

    return redirect('/dashboard')

# ================= UPDATE TASK ================= #

@app.route('/update_task/<int:id>', methods=['GET', 'POST'])
def update_task(id):

    task = Task.query.get(id)

    if request.method == 'POST':

        task.title = request.form['title']

        task.description = request.form['description']

        task.priority = request.form['priority']

        task.status = request.form['status']

        db.session.commit()

        return redirect('/dashboard')

    return render_template(
        'update_task.html',
        task=task
    )

# ================= DELETE TASK ================= #

@app.route('/delete_task/<int:id>')
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    return redirect('/dashboard')

# ================= LOGOUT ================= #

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ================= MAIN ================= #

if __name__ == '__main__':

    socketio.run(app, debug=True)