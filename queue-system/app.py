from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# ---------- DATABASE SETUP ----------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        number INTEGER,
        status TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS current_queue (
        current_number INTEGER
    )
    ''')

    c.execute("SELECT * FROM current_queue")
    if not c.fetchone():
        c.execute("INSERT INTO current_queue (current_number) VALUES (1)")

    conn.commit()
    conn.close()

init_db()

# ---------- AUTH ----------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = user[1]
            return redirect('/dashboard')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- DASHBOARD ----------

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT current_number FROM current_queue")
    current = c.fetchone()[0]

    c.execute("SELECT number FROM queue WHERE username=? AND status='Waiting'", (username,))
    result = c.fetchone()

    if result:
        user_number = result[0]
        people_ahead = user_number - current
    else:
        user_number = "Not in queue"
        people_ahead = "-"

    conn.close()

    return render_template('dashboard.html',
                           current=current,
                           user_number=user_number,
                           people_ahead=people_ahead)

# ---------- JOIN QUEUE ----------

@app.route('/join', methods=['GET', 'POST'])
def join():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        username = session['user']
        conn = get_db()
        c = conn.cursor()

        # Prevent duplicate
        c.execute("SELECT * FROM queue WHERE username=? AND status='Waiting'", (username,))
        if c.fetchone():
            conn.close()
            return redirect('/status')

        c.execute("SELECT MAX(number) FROM queue")
        last = c.fetchone()[0]
        next_number = 1 if last is None else last + 1

        c.execute("INSERT INTO queue (username, number, status) VALUES (?, ?, 'Waiting')",
                  (username, next_number))

        conn.commit()
        conn.close()

        return redirect('/status')

    return render_template('join_queue.html')

# ---------- STATUS ----------

@app.route('/status')
def status():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT current_number FROM current_queue")
    current = c.fetchone()[0]

    c.execute("SELECT number FROM queue WHERE username=? AND status='Waiting'", (username,))
    result = c.fetchone()

    if result:
        user_number = result[0]
        people_ahead = user_number - current
    else:
        user_number = "Not in queue"
        people_ahead = "-"

    conn.close()

    return render_template('queue_status.html',
                           current=current,
                           user_number=user_number,
                           people_ahead=people_ahead)

# ---------- RUN ----------

if __name__ == '__main__':
    app.run(debug=True)