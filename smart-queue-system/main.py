from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE CONNECTION
def db():
    return sqlite3.connect("queue.db")

# CREATE TABLES
def init():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        service TEXT,
        number INTEGER,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS current (
        service TEXT,
        current_number INTEGER
    )
    """)

    # Default services
    services = ['canteen', 'clinic', 'office']

    for service in services:
        c.execute("SELECT * FROM current WHERE service=?", (service,))
        if not c.fetchone():
            c.execute(
                "INSERT INTO current (service, current_number) VALUES (?, ?)",
                (service, 1)
            )

    conn.commit()
    conn.close()

init()

# ================= AUTH =================

@app.route('/', methods=['GET', 'POST'])
def auth():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        action = request.form['action']

        conn = db()
        c = conn.cursor()

        if action == 'register':

            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            flash("Registration successful!")

        else:

            c.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )

            user = c.fetchone()

            if not user:
                flash("Invalid login details")
                return redirect('/')

            flash("Login successful!")

        conn.commit()
        conn.close()

        session['user'] = username

        return redirect('/home')

    return render_template('auth.html')

# ================= HOME =================

@app.route('/home')
def home():

    if 'user' not in session:
        return redirect('/')

    username = session['user']

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT service, number
        FROM queue
        WHERE username=? AND status='waiting'
    """, (username,))

    queue_data = c.fetchone()

    if queue_data:

        service = queue_data[0]
        user_number = queue_data[1]

        c.execute("""
            SELECT current_number
            FROM current
            WHERE service=?
        """, (service,))

        current = c.fetchone()[0]

        people_ahead = user_number - current

    else:
        service = "-"
        current = "-"
        user_number = "-"
        people_ahead = "-"

    conn.close()

    return render_template(
        'home.html',
        current=current,
        user_number=user_number,
        people_ahead=people_ahead,
        service=service
    )

# ================= JOIN QUEUE =================

@app.route('/services', methods=['GET', 'POST'])
def services():

    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':

        service = request.form['service']
        username = session['user']

        conn = db()
        c = conn.cursor()

        # Prevent duplicate queue
        c.execute("""
            SELECT * FROM queue
            WHERE username=? AND status='waiting'
        """, (username,))

        if c.fetchone():
            flash("You are already in queue.")
            return redirect('/status')

        # Generate next queue number
        c.execute("""
            SELECT MAX(number)
            FROM queue
            WHERE service=?
        """, (service,))

        last = c.fetchone()[0]

        next_num = 1 if last is None else last + 1

        c.execute("""
            INSERT INTO queue
            (username, service, number, status)
            VALUES (?, ?, ?, 'waiting')
        """, (username, service, next_num))

        conn.commit()
        conn.close()

        flash("Successfully joined queue!")

        return redirect('/status')

    return render_template('services.html')

# ================= STATUS =================

@app.route('/status')
def status():

    if 'user' not in session:
        return redirect('/')

    username = session['user']

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT service, number
        FROM queue
        WHERE username=? AND status='waiting'
    """, (username,))

    queue_data = c.fetchone()

    if queue_data:

        service = queue_data[0]
        user_number = queue_data[1]

        c.execute("""
            SELECT current_number
            FROM current
            WHERE service=?
        """, (service,))

        current = c.fetchone()[0]

        people_ahead = user_number - current

        estimated_time = people_ahead * 5

    else:

        service = "-"
        user_number = "-"
        current = "-"
        people_ahead = "-"
        estimated_time = "-"

    conn.close()

    return render_template(
        'status.html',
        service=service,
        user_number=user_number,
        current=current,
        people_ahead=people_ahead,
        estimated_time=estimated_time
    )

# ================= ADMIN =================

@app.route('/admin')
def admin():

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT username, service, number, status
        FROM queue
    """)

    users = c.fetchall()

    conn.close()

    return render_template('admin.html', users=users)

# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged out successfully.")

    return redirect('/')

# ================= CANCEL QUEUE =================

@app.route('/cancel_queue')
def cancel_queue():
    if 'user' not in session:
        return redirect('/')

    username = session['user']
    
    conn = db()
    c = conn.cursor()
    
    # Remove the active 'waiting' entry for this user
    c.execute("""
        DELETE FROM queue 
        WHERE username=? AND status='waiting'
    """, (username,))
    
    conn.commit()
    conn.close()
    
    flash("You have left the queue. You can now select a new service.")
    return redirect('/services')
# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)