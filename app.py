from flask import Flask, render_template, request, session, redirect
import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()
app = Flask(__name__)

# Needed for sessions. Change this to any long random text.
app.secret_key =os.getenv("SECRET_KEY")


# ------------------------------------------------------------
# HOME
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------------------------------------
# SIGNUP
# ------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None
    if request.method == "POST":
        connection = psycopg2.connect(os.getenv("DATABASE_URL")
            )
        
        cursor = connection.cursor()
        
            # Create the tables (only if they do not exist yet)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100),
                    email VARCHAR(150) UNIQUE,
                    password TEXT,
                    role VARCHAR(20) DEFAULT 'user',
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
        
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        connection.commit()
        
        
        
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Check whether the email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            message = "This email is already registered."
        else:
            hashed_password = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                (username, email, hashed_password)
            )
            new_user = cursor.fetchone()

            # new_user is a tuple, so the id is new_user[0]
            cursor.execute(
                "INSERT INTO activity_logs (user_id, action) VALUES (%s, %s)",
                (new_user[0], "Created an account")
            )
            connection.commit()
                                                                            
        message = "Account created successfully. You can now log in."

        cursor.close()
        connection.close()

    return render_template("signup.html", message=message)


# ------------------------------------------------------------
# USER LOGIN
# ------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = psycopg2.connect(
            os.getenv("DATABASE_URL")
            )

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, username, email, password, role, status FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        # user[0] = id, user[1] = username, user[2] = email,
        # user[3] = password, user[4] = role, user[5] = status

        if user is None:
            message = "This email address is not registered."
        elif not check_password_hash(user[3], password):
            message = "Incorrect password. Please try again."
        elif user[5] != "active":
            message = "This account is inactive. Please contact an administrator."
        else:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[4]

            cursor.execute(
                "INSERT INTO activity_logs (user_id, action) VALUES (%s, %s)",
                (user[0], "Logged in")
            )
            connection.commit()

            role = user[4]

            cursor.close()
            connection.close()

            if role == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/dashboard")

        cursor.close()
        connection.close()

    return render_template("login.html", message=message)


# ------------------------------------------------------------
# USER DASHBOARD
# ------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin/dashboard")

    return render_template("dashboard.html", username=session["username"])


# ------------------------------------------------------------
# ADMIN LOGIN
# ------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    message = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = psycopg2.connect(
                os.getenv("DATABASE_URL")
            )

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, username, email, password, role, status FROM users WHERE email = %s AND role = 'admin'",
            (email,)
        )
        admin = cursor.fetchone()

        # admin[0] = id, admin[1] = username, admin[2] = email,
        # admin[3] = password, admin[4] = role, admin[5] = status

        if admin is None:
            message = "No administrator account was found with this email."
        elif not check_password_hash(admin[3], password):
            message = "Incorrect password. Please try again."
        elif admin[5] != "active":
            message = "This administrator account is inactive."
        else:
            session["user_id"] = admin[0]
            session["username"] = admin[1]
            session["role"] = admin[4]

            cursor.execute(
                "INSERT INTO activity_logs (user_id, action) VALUES (%s, %s)",
                (admin[0], "Administrator logged in")
            )
            connection.commit()

            cursor.close()
            connection.close()

            return redirect("/admin/dashboard")

        cursor.close()
        connection.close()

    return render_template("admin_login.html", message=message)


# ------------------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/admin/login")

    connection = psycopg2.connect(
            os.getenv("DATABASE_URL")
        )

    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    total_admins = cursor.fetchone()[0]

    # Each user row: [0] id, [1] username, [2] email, [3] role, [4] status, [5] created_at
    cursor.execute(
        "SELECT id, username, email, role, status, created_at FROM users ORDER BY id"
    )
    users = cursor.fetchall()

    # Each activity row: [0] username, [1] action, [2] created_at
    cursor.execute("""
        SELECT users.username, activity_logs.action, activity_logs.created_at
        FROM activity_logs
        JOIN users ON activity_logs.user_id = users.id
        ORDER BY activity_logs.id DESC
        LIMIT 10
    """)
    activities = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        username=session["username"],
        total_users=total_users,
        total_admins=total_admins,
        users=users,
        activities=activities
    )


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
