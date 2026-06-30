from flask import Flask, render_template, request, redirect, session
import sqlite3
import urllib.parse

app = Flask(__name__)
app.secret_key = "smartqueue123"

# Custom filter to safely parse spaces (e.g., "Deans Cafe") into valid URLs
@app.template_filter('urlencode')
def urlencode_filter(s):
    if s is None:
        return ""
    return urllib.parse.quote_plus(s)

def init_db():
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            location TEXT,
            number INTEGER
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS serving (
            location TEXT PRIMARY KEY,
            current_number INTEGER
        )
    """)
    
    locations = [
        "Deans Cafe",
        "Haji Tapah",
        "Dapur Sahang"
    ]
    
    for location in locations:
        c.execute(
            "INSERT OR IGNORE INTO serving(location, current_number) VALUES(?,0)",
            (location,)
        )
        
    conn.commit()
    conn.close()

# Automatically initialize database tables on startup
init_db()

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = sqlite3.connect("queue.db")
        c = conn.cursor()
        
        try:
            c.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            return "User already exists"
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            session["admin"] = True
            return redirect("/admin")
            
        conn = sqlite3.connect("queue.db")
        c = conn.cursor()
        
        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = c.fetchone()
        conn.close()
        
        if user:
            session["user"] = username
            session["admin"] = False
            return redirect("/dashboard")
            
        return "Invalid Login"
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    if session.get("admin"):
        return redirect("/admin")
        
    # The selection choices sent down to your dashboard HTML interface
    locations = ["Deans Cafe", "Haji Tapah", "Dapur Sahang"]
    return render_template("dashboard.html", user=session["user"], locations=locations)

@app.route("/take_number/<location>")
def take_number(location):
    if "user" not in session:
        return redirect("/login")
        
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()
    
    # 1. Stop double queuing if user already holds an active number
    c.execute(
        "SELECT * FROM queue WHERE username=? AND location=?",
        (session["user"], location)
    )
    existing = c.fetchone()
    
    if existing:
        conn.close()
        return "You already have a queue number for this location. <br><a href='/dashboard'>Back</a>"
        
    # 2. Get the next numerical ticket identifier safely
    c.execute(
        "SELECT MAX(number) FROM queue WHERE location=?",
        (location,)
    )
    row = c.fetchone()
    
    if row is None or row[0] is None:
        next_number = 1
    else:
        next_number = row[0] + 1
        
    # 3. Add to line ledger
    c.execute(
        "INSERT INTO queue(username,location,number) VALUES(?,?,?)",
        (session["user"], location, next_number)
    )
    
    conn.commit()
    conn.close()
    
    # Renders the styled modern digital ticket card receipt display page dynamically
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Queue Ticket Created</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            .ticket-container {{
                background: white;
                border-radius: 20px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
                overflow: hidden;
                animation: fadeInUp 0.5s ease-out;
            }}
            .ticket-header {{
                background: #f8fafc;
                padding: 30px 20px;
                text-align: center;
                border-bottom: 2px dashed #e2e8f0;
                position: relative;
            }}
            /* Cut-out circles on the sides to resemble a physical ticket */
            .ticket-header::before, .ticket-header::after {{
                content: '';
                position: absolute;
                bottom: -10px;
                width: 20px;
                height: 20px;
                background: #7153b6;
                border-radius: 50%;
            }}
            .ticket-header::before {{ left: -10px; }}
            .ticket-header::after {{ right: -10px; }}
            
            .brand-badge {{
                display: inline-block;
                background: #edf2f7;
                color: #4a5568;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-bottom: 12px;
            }}
            h1 {{
                color: #1a202c;
                font-size: 24px;
                margin: 0;
                font-weight: 700;
            }}
            .ticket-body {{
                padding: 40px 30px;
                text-align: center;
            }}
            .number-display {{
                background: linear-gradient(135deg, #f6f8ff 0%, #f1f4ff 100%);
                border: 2px solid #e0e6ff;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 25px;
            }}
            .number-label {{
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                color: #a0aec0;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .ticket-number {{
                font-size: 76px;
                font-weight: 800;
                color: #667eea;
                line-height: 1;
                margin: 0;
                text-shadow: 0 4px 10px rgba(102, 126, 234, 0.15);
            }}
            .instruction-text {{
                color: #718096;
                font-size: 15px;
                line-height: 1.6;
                margin: 0 0 35px 0;
            }}
            .back-btn {{
                display: inline-flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #5a71e0 100%);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 600;
                font-size: 16px;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .back-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 18px rgba(102, 126, 234, 0.4);
            }}
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="ticket-container">
            <div class="ticket-header">
                <span class="brand-badge">{location}</span>
                <h1>Smart Queue Ticket</h1>
            </div>
            <div class="ticket-body">
                <div class="number-display">
                    <div class="number-label">Your Turn Number</div>
                    <div class="ticket-number">#{next_number}</div>
                </div>
                <p class="instruction-text">
                    Ticket generated successfully. Please watch the display screen monitors for your turn status.
                </p>
                <a href="/dashboard" class="back-btn">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return "Access Denied"
        
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()
    
    locations = ["Deans Cafe", "Haji Tapah", "Dapur Sahang"]
    data = {}
    
    for location in locations:
        c.execute(
            "SELECT current_number FROM serving WHERE location=?",
            (location,)
        )
        serving = c.fetchone()[0]
        
        c.execute(
            "SELECT username, number FROM queue WHERE location=? ORDER BY number",
            (location,)
        )
        queue = c.fetchall()
        
        data[location] = {
            "serving": serving,
            "queue": queue
        }
        
    conn.close()
    return render_template("admin.html", data=data)

@app.route("/call_next/<location>")
def call_next(location):
    if not session.get("admin"):
        return "Access Denied"
        
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()
    
    c.execute(
        "SELECT id, number FROM queue WHERE location=? ORDER BY number LIMIT 1",
        (location,)
    )
    first = c.fetchone()
    
    if first:
        c.execute(
            "UPDATE serving SET current_number=? WHERE location=?",
            (first[1], location)
        )
        c.execute(
            "DELETE FROM queue WHERE id=?",
            (first[0],)
        )
        conn.commit()
        
    conn.close()
    return redirect("/admin")

@app.route("/now_serving")
def now_serving():
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()
    c.execute("SELECT location, current_number FROM serving")
    data = c.fetchall()
    conn.close()
    
    return render_template("now_serving.html", data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)