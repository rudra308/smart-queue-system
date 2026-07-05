# Group Project
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import urllib.parse
from datetime import datetime
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
app.secret_key = "smartqueue123"


# Zaiim - GPS System
SHOPS = {
    "Deans Cafe": {"lat": 2.927103731377013, "lon": 101.64179602864542},
    "Haji Tapah": {"lat": 2.9270903402387716, "lon":  101.64189642861923},
    "Dapur Sahang": {"lat": 2.9253397067904574, "lon": 101.6425604566883},
}

QUEUE_RADIUS_METERS = 200
GPS_ENABLED = True

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "queue.db"


def db():
    return sqlite3.connect(DB_PATH)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Return distance in meters between two GPS coordinates."""
    earth_radius_m = 6371000

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_m * c


@app.template_filter("urlencode")
def urlencode_filter(s):
    if s is None:
        return ""
    return urllib.parse.quote_plus(s)


def init_db():
    conn = db()
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
            number INTEGER,
            status TEXT DEFAULT 'waiting',
            created_at TEXT,
            served_at TEXT
        )
    """)


    for column_sql in [
        "ALTER TABLE queue ADD COLUMN status TEXT DEFAULT 'waiting'",
        "ALTER TABLE queue ADD COLUMN created_at TEXT",
        "ALTER TABLE queue ADD COLUMN served_at TEXT",
    ]:
        try:
            c.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS serving (
            location TEXT PRIMARY KEY,
            current_number INTEGER
        )
    """)

    locations = ["Deans Cafe", "Haji Tapah", "Dapur Sahang"]

    for location in locations:
        c.execute(
            "INSERT OR IGNORE INTO serving(location, current_number) VALUES(?, 0)",
            (location,)
        )

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return redirect("/login")


# Rudra - Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db()
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users(username, password) VALUES(?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Registration Failed</title>
                <style>
                    body{margin:0;font-family:Arial,sans-serif;background:linear-gradient(135deg,#11998e,#38ef7d);display:flex;justify-content:center;align-items:center;min-height:100vh;}
                    .card{background:white;width:90%;max-width:450px;padding:40px;border-radius:20px;text-align:center;box-shadow:0 15px 35px rgba(0,0,0,.25);}
                    .icon{font-size:70px;margin-bottom:15px;}
                    h1{color:#1e293b;margin-bottom:10px;}
                    p{color:#64748b;line-height:1.6;margin-bottom:30px;}
                    .btn{display:block;text-decoration:none;background:#11998e;color:white;padding:15px;border-radius:10px;font-weight:bold;}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="icon">⚠️</div>
                    <h1>Registration Failed</h1>
                    <p>That username is already taken. Please choose a different username and try again.</p>
                    <a href="/register" class="btn">Try Again</a>
                </div>
            </body>
            </html>
            """

    return render_template("register.html")


# Rudra - Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            session["admin"] = True
            return redirect("/admin")

        conn = db()
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

        return """
<!DOCTYPE html>
<html>
<head>
    <title>Login Failed</title>

    <style>
        body{
            margin:0;
            font-family:Arial,sans-serif;
            background:linear-gradient(135deg,#667eea,#764ba2);
            display:flex;
            justify-content:center;
            align-items:center;
            min-height:100vh;
        }

        .card{
            background:white;
            width:90%;
            max-width:450px;
            padding:40px;
            border-radius:20px;
            text-align:center;
            box-shadow:0 15px 35px rgba(0,0,0,.25);
        }

        .icon{
            font-size:70px;
            margin-bottom:15px;
        }

        h1{
            color:#1e293b;
            margin-bottom:10px;
        }

        p{
            color:#64748b;
            line-height:1.6;
            margin-bottom:30px;
        }

        .btn{
            display:block;
            text-decoration:none;
            background:#667eea;
            color:white;
            padding:15px;
            border-radius:10px;
            font-weight:bold;
            transition:.2s;
        }

        .btn:hover{
            background:#5a67d8;
        }
    </style>

</head>

<body>

<div class="card">

<div class="icon">❌</div>

<h1>Login Failed</h1>

<p>
The username or password you entered is incorrect.
Please check your credentials and try again.
</p>

<a href="/login" class="btn">
Try Again
</a>

</div>

</body>
</html>
"""

    return render_template("login.html")


# Rudra - Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if session.get("admin"):
        return redirect("/admin")

    locations = [
        "Deans Cafe",
        "Haji Tapah",
        "Dapur Sahang"
    ]

    return render_template(
        "dashboard.html",
        user=session["user"],
        locations=locations,
        gps_enabled=GPS_ENABLED
    )


@app.route("/services")
def services():
    return redirect("/dashboard")

@app.route("/take_number", methods=["POST"])
def take_number():
    if "user" not in session:
        return redirect("/login")

    data = request.get_json() or {}
    location = data.get("location")
    user_lat = data.get("latitude")
    user_lon = data.get("longitude")

    if location not in SHOPS:
        return """
        <html>
        <body style="font-family:Arial;text-align:center;padding:80px;">
            <h1>Location Error</h1>
            <p>Invalid shop selected.</p>
            <a href="/dashboard">Back to Dashboard</a>
        </body>
        </html>
        """

    # GPS CHECK ONLY RUNS WHEN GPS_ENABLED IS TRUE
    # Zaiim - GPS Verification
    if GPS_ENABLED:
        if user_lat is None or user_lon is None:
            return """
            <html>
            <body style="font-family:Arial;text-align:center;padding:80px;">
                <h1>GPS Error</h1>
                <p>Please allow location access to join the queue.</p>
                <a href="/dashboard">Back to Dashboard</a>
            </body>
            </html>
            """

        shop = SHOPS[location]

        distance = calculate_distance(
            user_lat,
            user_lon,
            shop["lat"],
            shop["lon"]
        )

        if distance > QUEUE_RADIUS_METERS:
            remaining = max(0, round(distance - QUEUE_RADIUS_METERS))

            return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Location Verification Failed</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <style>
            *{{box-sizing:border-box;}}

            body{{
                margin:0;
                font-family:'Segoe UI',Arial,sans-serif;
                background:linear-gradient(135deg,#fee2e2,#ede9fe);
                min-height:100vh;
                display:flex;
                justify-content:center;
                align-items:center;
                padding:20px;
            }}

            .card{{
                background:white;
                width:100%;
                max-width:620px;
                border-radius:24px;
                padding:38px 32px;
                text-align:center;
                box-shadow:0 20px 45px rgba(0,0,0,.18);
            }}

            .icon{{
                width:95px;
                height:95px;
                border-radius:50%;
                background:#fee2e2;
                display:flex;
                align-items:center;
                justify-content:center;
                margin:0 auto 20px;
                font-size:50px;
            }}

            h1{{
                margin:0;
                color:#0f172a;
                font-size:34px;
            }}

            .subtitle{{
                color:#64748b;
                font-size:18px;
                margin:14px 0 28px;
            }}

            .subtitle b{{
                color:#dc2626;
            }}

            .radius-box{{
                background:#fff1f2;
                border:1px solid #fecdd3;
                color:#334155;
                padding:18px;
                border-radius:16px;
                font-size:18px;
                margin-bottom:22px;
            }}

            .radius-box b{{
                color:#dc2626;
            }}

            .stats{{
                display:grid;
                grid-template-columns:1fr 1fr;
                gap:16px;
                margin-bottom:22px;
            }}

            .stat{{
                border:1px solid #e2e8f0;
                border-radius:16px;
                padding:22px 14px;
                background:#ffffff;
            }}

            .stat-icon{{
                font-size:32px;
                margin-bottom:8px;
            }}

            .number{{
                font-size:40px;
                font-weight:900;
                color:#dc2626;
                line-height:1;
            }}

            .orange{{
                color:#f59e0b;
            }}

            .label{{
                color:#334155;
                font-size:15px;
                margin-top:8px;
            }}

            .note{{
                background:#eff6ff;
                border:1px solid #bfdbfe;
                color:#1e3a8a;
                padding:16px;
                border-radius:14px;
                margin-bottom:24px;
                line-height:1.5;
            }}

            .btn{{
                display:block;
                text-decoration:none;
                background:linear-gradient(135deg,#667eea,#764ba2);
                color:white;
                padding:16px;
                border-radius:14px;
                font-weight:bold;
                font-size:17px;
                box-shadow:0 10px 22px rgba(102,126,234,.35);
                transition:.25s;
            }}

            .btn:hover{{
                transform:translateY(-2px);
            }}

            @media(max-width:520px){{
                h1{{font-size:28px;}}
                .stats{{grid-template-columns:1fr;}}
                .card{{padding:32px 22px;}}
            }}
        </style>
    </head>

    <body>
        <div class="card">
            <div class="icon">📍</div>

            <h1>Location Verification Failed</h1>

            <p class="subtitle">
                You are too far from <b>{location}</b>.
            </p>

            <div class="radius-box">
                Queue numbers can only be collected within
                <b>{QUEUE_RADIUS_METERS} metres</b>.
            </div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-icon">📌</div>
                    <div class="number">{round(distance)}</div>
                    <div class="label">metres away</div>
                </div>

                <div class="stat">
                    <div class="stat-icon">↙️</div>
                    <div class="number orange">{remaining}</div>
                    <div class="label">metres closer needed</div>
                </div>
            </div>

            <div class="note">
                Please move closer to the selected shop location and try again.
            </div>

            <a href="/dashboard" class="btn">🏠 Return to Dashboard</a>
        </div>
    </body>
    </html>
    """
    else:
        distance = 0

    conn = db()
    c = conn.cursor()

    c.execute(
        "SELECT * FROM queue WHERE username=? AND status='waiting'",
        (session["user"],)
    )
    existing = c.fetchone()

    if existing:
        conn.close()
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Already in Queue</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">

            <style>
                *{box-sizing:border-box;}

                body{
                    margin:0;
                    font-family:'Segoe UI',Arial,sans-serif;
                    background:linear-gradient(135deg,#667eea,#764ba2);
                    min-height:100vh;
                    display:flex;
                    justify-content:center;
                    align-items:center;
                    padding:20px;
                }

                .card{
                    background:white;
                    width:100%;
                    max-width:430px;
                    border-radius:22px;
                    padding:38px 28px;
                    text-align:center;
                    box-shadow:0 18px 40px rgba(0,0,0,.28);
                }

                .icon{
                    font-size:75px;
                    margin-bottom:15px;
                }

                h1{
                    margin:0;
                    color:#1e293b;
                    font-size:30px;
                }

                p{
                    color:#64748b;
                    font-size:16px;
                    line-height:1.6;
                    margin:18px 0 28px;
                }

                .notice{
                    background:#fff7ed;
                    color:#c2410c;
                    border:1px solid #fed7aa;
                    padding:14px;
                    border-radius:12px;
                    font-weight:bold;
                    margin-bottom:25px;
                }

                .btn{
                    display:block;
                    text-decoration:none;
                    padding:15px;
                    border-radius:12px;
                    font-weight:bold;
                    margin-top:12px;
                    transition:.25s;
                }

                .btn:hover{
                    transform:translateY(-2px);
                }

                .primary{
                    background:#667eea;
                    color:white;
                }

                .secondary{
                    background:#f1f5f9;
                    color:#334155;
                }
            </style>
        </head>

        <body>
            <div class="card">
                <div class="icon">🎫</div>

                <h1>You Are Already in a Queue</h1>

                <p>
                    You already have an active queue ticket.
                    Please check your current queue status before joining another queue.
                </p>

                <div class="notice">
                    Only one active queue ticket is allowed at a time.
                </div>

                <a href="/status" class="btn primary">View My Status</a>
                <a href="/dashboard" class="btn secondary">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """

    c.execute(
        "SELECT MAX(number) FROM queue WHERE location=?",
        (location,)
    )
    row = c.fetchone()

    next_number = 1 if row is None or row[0] is None else row[0] + 1
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        """
        INSERT INTO queue(username, location, number, status, created_at, served_at)
        VALUES (?, ?, ?, 'waiting', ?, ?)
        """,
        (session["user"], location, next_number, created_at, None)
    )

    conn.commit()
    conn.close()

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Queue Ticket Created</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        * {{ box-sizing: border-box; }}

        body {{
            margin: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}

        .ticket-card {{
            background: white;
            width: 100%;
            max-width: 430px;
            border-radius: 22px;
            overflow: hidden;
            box-shadow: 0 18px 40px rgba(0,0,0,0.28);
            text-align: center;
        }}

        .ticket-header {{
            background: linear-gradient(135deg,#4f46e5,#6366f1);
             color:white;
            padding:35px 20px;
        }}

        .badge {{
            display: inline-block;
            background:rgba(255,255,255,.18);
             color:white;
            padding: 7px 16px;
            border:1px solid rgba(255,255,255,.3);
            font-weight: 800;
            font-size: 13px;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}

        .ticket-body {{
            padding: 35px 28px;
        }}

        h1 {{
            margin: 0;
            color: #1e293b;
        }}

        .ticket-number {{
            font-size: 100px;
            font-weight: 900;
            color: #4f46e5;
            margin: 25px 0;
            letter-spacing: 3px;
        }}

        .verified {{
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
            margin-bottom: 22px;
        }}

        .btn {{
            display: block;
            text-decoration: none;
            padding: 14px;
            border-radius: 10px;
            font-weight: bold;
            margin-top: 12px;
        }}

        .primary {{
            background: #667eea;
            color: white;
        }}

        .secondary {{
            background: #f1f5f9;
            color: #334155;
        }}
    </style>
</head>

<body>
    <div class="ticket-card">
        <div class="ticket-header">
            <div class="badge">{location}</div>
            <div style="font-size:70px;margin-bottom:10px;">🎟️</div>
            <h1>Smart Queue Ticket</h1>
        </div>

        <div class="ticket-body">
            <p style="font-size:18px;color:#64748b;">
            You have successfully joined
            </p>

            <h2 style="margin-top:5px;color:#1e293b;">
            {location}
            </h2>

            <div class="ticket-number">#{next_number}</div>

            <div class="verified">
                {"✅ GPS Verified (" + str(round(distance)) + " m from shop)" if GPS_ENABLED else "⚙️ GPS verification disabled by administrator"}
            </div>

            <div style="
                background:#f8fafc;
                padding:15px;
                border-radius:12px;
                margin-top:20px;
                margin-bottom:20px;
            ">
                <b>Estimated Waiting Time</b><br>
                Approximately {(next_number - 1) * 5} minutes
            </div>

            <a href="/status" class="btn primary">View My Status</a>
            <a href="/dashboard" class="btn secondary">Back to Dashboard</a>

                    </div>
                </div>
            </body>
            </html>
            """

@app.route("/take_number/<location>")
def old_take_number_link(location):
    return redirect("/dashboard")


# Rudra - Admin Panel
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return "Access Denied"

    conn = db()
    c = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")
        location = request.form.get("service")

        if action == "next":
            c.execute("""
                SELECT id, number
                FROM queue
                WHERE location=? AND status='waiting'
                ORDER BY number
                LIMIT 1
            """, (location,))
            first = c.fetchone()

            if first:
                served_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                c.execute(
                    "UPDATE serving SET current_number=? WHERE location=?",
                    (first[1], location)
                )

                c.execute(
                    "UPDATE queue SET status='served', served_at=? WHERE id=?",
                    (served_at, first[0])
                )

        elif action == "reset":
            c.execute("DELETE FROM queue")
            c.execute("UPDATE serving SET current_number = 0")

        conn.commit()

    c.execute("SELECT username, location, number, status FROM queue ORDER BY id DESC")
    users = c.fetchall()

    c.execute("SELECT location, current_number FROM serving")
    current_numbers = c.fetchall()

    c.execute("SELECT COUNT(*) FROM queue WHERE status='waiting'")
    total_waiting = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queue WHERE status='served'")
    total_served = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queue WHERE status='cancelled'")
    total_cancelled = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queue WHERE location='Deans Cafe' AND status='waiting'")
    canteen_waiting = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queue WHERE location='Haji Tapah' AND status='waiting'")
    clinic_waiting = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queue WHERE location='Dapur Sahang' AND status='waiting'")
    office_waiting = c.fetchone()[0]

    conn.close()

    return render_template(
    "admin.html",
    users=users,
    current_numbers=current_numbers,
    total_waiting=total_waiting,
    total_served=total_served,
    total_cancelled=total_cancelled,
    canteen_waiting=canteen_waiting,
    clinic_waiting=clinic_waiting,
    office_waiting=office_waiting,
    gps_enabled=GPS_ENABLED
)


@app.route("/call_next/<location>")
def call_next(location):
    if not session.get("admin"):
        return "Access Denied"

    conn = db()
    c = conn.cursor()

    c.execute(
        "SELECT id, number FROM queue WHERE location=? AND status='waiting' ORDER BY number LIMIT 1",
        (location,)
    )
    first = c.fetchone()

    if first:
        served_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            "UPDATE serving SET current_number=? WHERE location=?",
            (first[1], location)
        )

        c.execute(
            "UPDATE queue SET status='served', served_at=? WHERE id=?",
            (served_at, first[0])
        )

        conn.commit()

    conn.close()
    return redirect("/admin")


@app.route("/now_serving")
def now_serving():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT location, current_number FROM serving")
    data = c.fetchall()
    conn.close()

    return render_template("now_serving.html", data=data)


# Zaiim - User Status
@app.route("/status")
def status():
    if "user" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT location, number, created_at
        FROM queue
        WHERE username=? AND status='waiting'
    """, (session["user"],))
    queue_data = c.fetchone()

    if queue_data:
        location = queue_data[0]
        user_number = queue_data[1]
        created_at = queue_data[2]

        c.execute(
            "SELECT current_number FROM serving WHERE location=?",
            (location,)
        )
        current = c.fetchone()[0]

        people_ahead = max(user_number - current, 0)
        estimated_time = people_ahead * 5
    else:
        location = "-"
        user_number = "-"
        current = "-"
        people_ahead = "-"
        estimated_time = "-"
        created_at = "-"

    conn.close()

    return render_template(
        "status.html",
        service=location,
        user_number=user_number,
        current=current,
        people_ahead=people_ahead,
        estimated_time=estimated_time,
        created_at=created_at
    )


@app.route("/cancel_queue", methods=["POST"])
def cancel_queue():
    if "user" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()

    c.execute("""
        UPDATE queue
        SET status='cancelled'
        WHERE username=? AND status='waiting'
    """, (session["user"],))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# Zaiim - Queue History
@app.route("/history")
def history():
    if not session.get("admin"):
        return "Access Denied"

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT username, location, number, status, created_at, served_at
        FROM queue
        ORDER BY id DESC
    """)
    history_data = c.fetchall()

    conn.close()

    return render_template("history.html", history_data=history_data)


# Zaiim - GPS Toggle
@app.route("/toggle_gps")
def toggle_gps():
    global GPS_ENABLED

    if not session.get("admin"):
        return "Access Denied"

    GPS_ENABLED = not GPS_ENABLED

    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    print("Smart Queue running: http://127.0.0.1:5000/login")
    print("Admin login: username=admin password=admin123")
    app.run(debug=True)
