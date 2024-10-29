from flask import Flask, render_template, request, redirect, url_for
import sqlite3
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS tasks (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   status TEXT DEFAULT 'pending',
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')
    conn.commit()
    conn.close()

init_db()

# Temp data store
tasks = []

@app.route('/')
def home():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    if task:
        # tasks.append(task)
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (title) VALUES (?)', (task,))
        conn.commit()
        conn.close()
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 0<=task_id<len(tasks):
        tasks.pop(task_id)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)