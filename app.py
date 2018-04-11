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
app.config['MYSQL_DB'] = 'SegFault'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)


# Redirecting to Home page
@app.route('/')
def index():
    return render_template('home.html')

# Redirecting to the about page
@app.route('/about')
def about():
    return render_template('about.html')

# Running the app if app.py is the main module
if __name__ == '__main__':
    # Encryption Key
    app.secret_key = 'secret123'

    # Starting the app
    app.run()
