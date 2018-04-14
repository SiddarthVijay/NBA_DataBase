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
@app.route('/', methods=['GET', 'POST'])
def index():
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
                return render_template('home.html', error=error)

            # Close the connection to the database
            cur.close()
        else:
            error = 'Username Not Found'
            return render_template('home.html', error=error)

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


# Accessing the user profile
@app.route('/profile')
@is_loggedin
def profile():
    # cursor
    cur = mysql.connection.cursor()
    username = session['username']

    # Get user by username
    result = cur.execute("SELECT * FROM users where user_username = %s", [username])
    if result > 0:
        data = cur.fetchone()
        name = data['user_name']
        email = data['user_email']
        id = data['user_id']
        date = data['register_date']

    return render_template('profile.html', name=name, email=email, id=id, date=date)


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


# Question Class
class QuestionForm(Form):
    statement = StringField('Question', [validators.Length(min=1, max=280)])
    body = TextAreaField('Description', [validators.Length(max=500)])


# Add Question Page
@app.route('/addquestion', methods=['GET', 'POST'])
@is_loggedin
def addquestion():
    form = QuestionForm(request.form)
    if request.method == 'POST' and form.validate():
        statement = form.statement.data
        body = form.body.data
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO questions(statement,body,poster) VALUES(%s, %s, %s)",(statement, body, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('Question Posted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('addquestion.html', form=form)


@app.route('/questions')
def question():
    cur = mysql.connection.cursor()


    result = cur.execute("SELECT * FROM questions ORDER BY id DESC")


    qs = cur.fetchall()
    if result > 0:
        return render_template('questions.html', qs=qs)
    else:
        msg = "No article found"
        return render_template('questions.html',msg=msg)
    cur.close()


# Comment form
class CommentForm(Form):
    body = TextAreaField('Comment',[validators.Length(max=80)])

@app.route('/question/<string:id>/',methods = ['GET','POST'])
def questions(id):

    cur = mysql.connection.cursor()

    if not 'logged_in' in session :
        username = None
    else:
        username = session['username']

    cur.execute("SELECT * FROM questions WHERE id = %s",[id])
    one_qs = cur.fetchone()
    cur.close()

    cur = mysql.connection.cursor()
    auths = cur.execute("SELECT * FROM answers WHERE (author,qid) = (%s,%s)",([session['username']],[id]))
    cur.close()

    cur2 = mysql.connection.cursor()

    result = cur2.execute("SELECT * FROM answers WHERE qid = %s ORDER BY id DESC",[id])
    answers = cur2.fetchall()
    cur2.close()

    comments = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM answers WHERE qid = %s ORDER BY id DESC",[id])
    for row in cur:
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM comments WHERE ansid = %s",[row['id']])
        comments.append(cur2.fetchall())
        cur2.close()
    cur.close()

    form = CommentForm(request.form)
    if request.method == 'POST' and form.validate():
        body = form.body.data
        
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO comments(ansid,body,author) VALUES(%s, %s, %s)",([answer['id']], body, session['username']))

        mysql.connection.commit()
        cur.close()

        flash('Comment Posted', 'success')
        return redirect(url_for('questions'))

    if result > 0:
        return render_template('question.html', form=form, one_qs=one_qs, answers=answers, username=username, auths=auths, comments=comments)
    else:
        msg = "Not Answered Yet"
        return render_template('question.html', form=form, one_qs=one_qs, msg=msg, username=username, auths=auths, comments=comments)


class AnswerForm(Form):
    body = TextAreaField('Your Answer:',[validators.Length(min=5)])


@app.route('/addanswer/<string:id>', methods=['GET', 'POST'])
@is_loggedin
def addanswer(id):
    form = AnswerForm(request.form)
    cur2 = mysql.connection.cursor()

    result = cur2.execute("SELECT * FROM questions WHERE id = %s",[id])
    one_qs = cur2.fetchone()

    cur2.close()

    if request.method == 'POST' and form.validate():
        body = form.body.data
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO answers(qid,body,author) VALUES(%s, %s, %s)",([id], body, session['username']))
        mysql.connection.commit()
        cur.close()

        flash('Question Answered', 'success')
        return redirect(url_for('dashboard'))
    return render_template('addanswer.html', form=form ,one_qs=one_qs)


# Running the app if app.py is the main module
if __name__ == '__main__':
    # Encryption Key
    app.secret_key='bZ\x85\xb2\xfc1$\xe6\n\xa1\xc0\xce\xdd\x9f\x815\xc0\xe4\xac\xc6\xfc\x0e\xa9\xa0V'

    # Starting the app
    app.run()
