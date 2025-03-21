from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from contextlib import closing

app = Flask(__name__, static_folder='static')
app.secret_key = "supersecretkey"

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_db_connection()) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                class TEXT NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

init_db()

# Predefined chapters
CHAPTERS = {
    "11": {
        "Physics": [
            "Physical World", "Units and Measurements", "Motion in a Straight Line", "Motion in a Plane",
            "Laws of Motion", "Work, Energy, and Power", "System of Particles and Rotational Motion",
            "Gravitation", "Mechanical Properties of Solids", "Mechanical Properties of Fluids",
            "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"
        ],
        "Chemistry": [
            "Some Basic Concepts of Chemistry", "Structure of Atom", "Classification of Elements and Periodicity in Properties",
            "Chemical Bonding and Molecular Structure", "States of Matter: Gases and Liquids", "Thermodynamics",
            "Equilibrium", "Redox Reactions", "Hydrogen", "The s-Block Elements", "The p-Block Elements",
            "Organic Chemistry: Some Basic Principles and Techniques", "Hydrocarbons", "Environmental Chemistry"
        ],
        "Mathematics": [
            "Sets", "Relations and Functions", "Trigonometric Functions", "Complex Numbers and Quadratic Equations",
            "Linear Inequalities", "Permutations and Combinations", "Binomial Theorem", "Sequences and Series",
            "Straight Lines", "Conic Sections", "Introduction to Three-Dimensional Geometry",
            "Limits and Derivatives", "Mathematical Reasoning", "Statistics", "Probability"
        ]
    },
    "12": {
        "Physics": [
            "Electric Charges and Fields", "Electrostatic Potential and Capacitance", "Current Electricity",
            "Moving Charges and Magnetism", "Magnetism and Matter", "Electromagnetic Induction",
            "Alternating Current", "Electromagnetic Waves", "Ray Optics and Optical Instruments",
            "Wave Optics", "Dual Nature of Radiation and Matter", "Atoms", "Nuclei",
            "Semiconductor Electronics", "Communication Systems"
        ],
        "Chemistry": [
            "The Solid State", "Solutions", "Electrochemistry", "Chemical Kinetics", "Surface Chemistry",
            "General Principles and Processes of Isolation of Elements", "The p-Block Elements",
            "The d- and f-Block Elements", "Coordination Compounds", "Haloalkanes and Haloarenes",
            "Alcohols, Phenols, and Ethers", "Aldehydes, Ketones, and Carboxylic Acids",
            "Organic Compounds Containing Nitrogen", "Biomolecules", "Polymers", "Chemistry in Everyday Life"
        ],
        "Mathematics": [
            "Relations and Functions", "Inverse Trigonometric Functions", "Matrices", "Determinants",
            "Continuity and Differentiability", "Application of Derivatives", "Integrals",
            "Application of Integrals", "Differential Equations", "Vector Algebra",
            "Three-Dimensional Geometry", "Linear Programming", "Probability"
        ]
    }
}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with closing(get_db_connection()) as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists!')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with closing(get_db_connection()) as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            if user:
                return redirect(url_for('dashboard', user_id=user['id']))
            else:
                flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    with closing(get_db_connection()) as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        progress = conn.execute('SELECT * FROM progress WHERE user_id = ?', (user_id,)).fetchall()
    return render_template('dashboard.html', user=user, progress=progress, chapters=CHAPTERS)

@app.route('/mark_complete/<int:user_id>/<string:class_name>/<string:subject>/<string:chapter>')
def mark_complete(user_id, class_name, subject, chapter):
    with closing(get_db_connection()) as conn:
        conn.execute('''
            INSERT INTO progress (user_id, class, subject, chapter, completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, class_name, subject, chapter, 1))
        conn.commit()
    return redirect(url_for('dashboard', user_id=user_id))

@app.route('/leaderboard')
def leaderboard():
    with closing(get_db_connection()) as conn:
        leaderboard_data = conn.execute('''
            SELECT users.username, COUNT(progress.id) AS completed
            FROM users
            LEFT JOIN progress ON users.id = progress.user_id AND progress.completed = 1
            GROUP BY users.id
            ORDER BY completed DESC
            LIMIT 10
        ''').fetchall()
    return render_template('leaderboard.html', leaderboard=leaderboard_data, enumerate=enumerate)

@app.route('/todo/<int:user_id>')
def todo(user_id):
    with closing(get_db_connection()) as conn:
        todos = conn.execute('SELECT * FROM todos WHERE user_id = ?', (user_id,)).fetchall()
    return render_template('todo.html', user_id=user_id, todos=todos)

@app.route('/add_todo/<int:user_id>', methods=['POST'])
def add_todo(user_id):
    task = request.form['task']
    with closing(get_db_connection()) as conn:
        conn.execute('INSERT INTO todos (user_id, task) VALUES (?, ?)', (user_id, task))
        conn.commit()
    return redirect(url_for('todo', user_id=user_id))

@app.route('/delete_todo/<int:todo_id>/<int:user_id>')
def delete_todo(todo_id, user_id):
    with closing(get_db_connection()) as conn:
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
    return redirect(url_for('todo', user_id=user_id))

@app.route('/toggle_todo/<int:todo_id>/<int:user_id>')
def toggle_todo(todo_id, user_id):
    with closing(get_db_connection()) as conn:
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
        new_status = not todo['completed']
        conn.execute('UPDATE todos SET completed = ? WHERE id = ?', (new_status, todo_id))
        conn.commit()
    return redirect(url_for('todo', user_id=user_id))

if __name__ == '__main__':
    app.run(debug=True)