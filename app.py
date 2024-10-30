from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from flask_bcrypt import Bcrypt
from flask_session import Session

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
bcrypt = Bcrypt(app)

def init_db():
    """
    Initialize the database with necessary tables.
    """
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'member'  -- Can be 'admin' or 'member'
        )
    ''')
    
    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- 'pending', 'in progress', or 'completed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'member')  # Default role is 'member'
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_pw, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists. Please choose another one."
        finally:
            conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[3]  # Add role to the session
            return redirect(url_for('home'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Home route
@app.route('/')
def home():
    if 'user_id' not in session or session['user_id'] is None:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects')
    projects = cursor.fetchall()
    conn.close()
    return render_template('index.html', projects=projects)

# Project creation route (Admin only)
@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO projects (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('create_project.html')

# Project viewing route
@app.route('/projects/<int:project_id>')
def view_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    cursor.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_project.html', project=project, tasks=tasks)

# Add task route
@app.route('/projects/<int:project_id>/add_task', methods=['GET', 'POST'])
def add_task(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        conn = sqlite3.connect('project_management.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (project_id, user_id, title) VALUES (?, ?, ?)', (project_id, session['user_id'], title))
        conn.commit()
        conn.close()
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('add_task.html', project_id=project_id)

# Edit task route
@app.route('/projects/<int:project_id>/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(project_id, task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ? AND project_id = ?', (task_id, project_id))
    task = cursor.fetchone()
    
    if request.method == 'POST':
        new_title = request.form['title']
        new_status = request.form['status']
        cursor.execute('UPDATE tasks SET title = ?, status = ? WHERE id = ?', (new_title, new_status, task_id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_project', project_id=project_id))
    
    conn.close()
    return render_template('edit_task.html', task=task, project_id=project_id)

# Delete task route
@app.route('/projects/<int:project_id>/delete_task/<int:task_id>')
def delete_task(project_id, task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND project_id = ?', (task_id, project_id))
    conn.commit()
    conn.close()
    return redirect(url_for('view_project', project_id=project_id))

# View tasks by project route
@app.route('/projects/<int:project_id>/tasks')
def view_tasks_by_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_tasks.html', tasks=tasks, project_id=project_id)

# View projects by user route
@app.route('/user/projects')
def view_projects_by_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects WHERE id IN (SELECT project_id FROM tasks WHERE user_id = ?)', (session['user_id'],))
    projects = cursor.fetchall()
    conn.close()
    return render_template('view_user_projects.html', projects=projects)

# View tasks by user route
@app.route('/user/tasks')
def view_tasks_by_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_user_tasks.html', tasks=tasks)

# View tasks by status route
@app.route('/tasks/status/<string:status>')
def view_tasks_by_status(status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE status = ?', (status,))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_tasks_by_status.html', tasks=tasks, status=status)

# View tasks by project and status route
@app.route('/projects/<int:project_id>/tasks/status/<string:status>')
def view_tasks_by_project_and_status(project_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE project_id = ? AND status = ?', (project_id, status))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_tasks_by_project_and_status.html', tasks=tasks, project_id=project_id, status=status)

# View projects by status route
@app.route('/projects/status/<string:status>')
def view_projects_by_status(status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects WHERE id IN (SELECT project_id FROM tasks WHERE status = ?)', (status,))
    projects = cursor.fetchall()
    conn.close()
    return render_template('view_projects_by_status.html', projects=projects, status=status)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
