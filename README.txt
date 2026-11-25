SIMPLE FLASK + POSTGRESQL USER MANAGEMENT SYSTEM
================================================

1. INSTALL THE REQUIREMENTS
---------------------------
Open a terminal in the Simple_Flask_Project folder and run:

    pip install -r requirements.txt


2. CREATE AN EMPTY DATABASE IN PGADMIN
--------------------------------------
- Open pgAdmin and connect to your local server.
- Right-click "Databases" -> Create -> Database...
- Give it a name (for example: flask_users) and click Save.
- Leave it empty. The app creates the tables for you.


3. ENTER YOUR DATABASE NAME AND PASSWORD
----------------------------------------
Open app.py. Every route that talks to PostgreSQL has this block:

    connection = psycopg2.connect(
        host="localhost",
        database="YOUR_DATABASE_NAME",
        user="postgres",
        password="YOUR_POSTGRES_PASSWORD",
        port="5432"
    )

There are 4 of these blocks (signup, login, admin_login, admin_dashboard).
In ALL 4, replace YOUR_DATABASE_NAME and YOUR_POSTGRES_PASSWORD with your
real details. (Tip: use Find and Replace in your editor.)

Also change app.secret_key near the top of app.py to any secret text.


4. RUN THE APP
--------------
    python app.py

Flask will start at http://127.0.0.1:5000


5. WHICH ROUTE TO VISIT FIRST
-----------------------------
The home page (http://127.0.0.1:5000/) is a landing page with buttons to
Sign up and Log in. But visit this first so the tables get created:

    http://127.0.0.1:5000/signup

This is important because the signup route creates the tables.


6. HOW THE TABLES ARE CREATED
-----------------------------
Inside the signup route, cursor.execute() runs two
"CREATE TABLE IF NOT EXISTS" statements (users and activity_logs),
followed by connection.commit(). Each time /signup is opened the tables
are created if they are missing, and left alone if they already exist.


7. REGISTER AN ORDINARY USER
----------------------------
- Go to /signup, enter a username, email and password, and submit.
- You will see "Account created successfully."
- Go to /login and log in. You will be sent to /dashboard.


8. MAKE A USER AN ADMINISTRATOR (PGADMIN)
-----------------------------------------
- Register the user first at /signup.
- In pgAdmin: right-click your database -> Query Tool.
- Run this (replace the email with the registered user's real email):

    UPDATE users
    SET role = 'admin'
    WHERE email = 'your-email@example.com';

- Click the Execute (play) button.
- Now go to http://127.0.0.1:5000/admin/login and log in with that
  email and password. You will be sent to /admin/dashboard.
  (Logging in at /login with an admin account also sends you there.)


ROUTES
------
/                 -> landing page (index.html)
/signup           -> create account (also creates the tables)
/login            -> user login
/dashboard        -> user dashboard
/admin/login      -> administrator login
/admin/dashboard  -> administrator dashboard
/logout           -> clears the session, returns to /login
