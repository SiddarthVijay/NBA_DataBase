# Imports from Flask
from flask import Flask
from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import session
from flask import logging
from flask import request

# Imports for MySQL
from flask_mysqldb import MySQL

# Imports for wtforms
from wtforms import Form
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import validators

# Imports from passlib
from passlib.hash import sha256_crypt

# Imports from Functools
from functools import wraps

app = Flask(__name__)
app.debug = True

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'segfault'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)


# Registration Form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('E-Mail', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# Check if user logged in
def is_loggedin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login first', 'danger')
            return redirect(url_for('login'))
    return wrap


# Redirecting to Home page
@app.route('/')
def index():
    return render_template('home.html')


# Redirecting to the about page
@app.route('/about')
def about():
    return render_template('about.html')


# Redirecting to the dashboard
@app.route('/dashboard')
@is_loggedin
def dashboard():
    return render_template('dashboard.html')


# Register page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create a Cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(user_name, user_email, user_username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and you can login', 'success')

        return redirect(url_for('index'))
    return render_template('signup.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users where user_username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Correct password
                session['logged_in'] = True
                session['username'] = username

                # Flash will flash a message
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Wrong Password'
                return render_template('login.html', error=error)

            # Close the connection to the database
            cur.close()
        else:
            error = 'Username Not Found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Logout
@app.route('/logout')
@is_loggedin
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Running the app if app.py is the main module
if __name__ == '__main__':
    # Encryption Key
    app.secret_key='bZ\x85\xb2\xfc1$\xe6\n\xa1\xc0\xce\xdd\x9f\x815\xc0\xe4\xac\xc6\xfc\x0e\xa9\xa0V'

    # Starting the app
    app.run()
