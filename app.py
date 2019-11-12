# Imports from Flask
from flask import Flask
from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import session
from flask import logging
from flask import request
from json import *
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

from math import floor

app = Flask(__name__)
app.debug = True

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'DBpass123!'
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
    friends = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT statement FROM questions")

    for row in cur:
        friends.append(row['statement'])
    cur.close()

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
                return render_template('home.html',friends=friends, error=error)

            # Close the connection to the database
            cur.close()
        else:
            error = 'Username Not Found'
            return render_template('home.html',friends=friends, error=error)

    return render_template('home.html',friends=friends)


# Redirecting to the about page
@app.route('/about')
def about():
    return render_template('about.html')


# Redirecting to the dashboard
@app.route('/dashboard')
@is_loggedin
def dashboard():
    username = session['username']
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Players
    player_results = cur.execute("SELECT * FROM Player where Posted_By = %s", [username])
    players = cur.fetchall()

    # Get Coaches
    coaches_results = cur.execute("SELECT * FROM Coach where Posted_By = %s", [username])
    coaches = cur.fetchall()

    # Get Owner
    owners_results = cur.execute("SELECT * FROM Owner where Posted_By = %s", [username])
    owners = cur.fetchall()

    # Get MVP
    mvps_results = cur.execute("SELECT * FROM MVP where Posted_By = %s", [username])
    mvps = cur.fetchall()

    # Get DPOY
    dpoys_results = cur.execute("SELECT * FROM DPOY where Posted_By = %s", [username])
    dpoys = cur.fetchall()

    # Get Champions
    champions_results = cur.execute("SELECT * FROM Championship where Posted_By = %s", [username])
    champions = cur.fetchall()

    # Get user by username
    user_results = cur.execute("SELECT * FROM users where user_username = %s", [username])
    if user_results > 0:
        user = cur.fetchone()
        name = user['user_name']

    return render_template('dashboard.html', name=name, players=players, coaches=coaches, owners=owners, mvps=mvps, dpoys=dpoys, champions=champions)


# Accessing the user profile
@app.route('/profile')
@is_loggedin
def profile():
 # cursor
    cur = mysql.connection.cursor()
    username = session['username']
    no_questions = 0
    no_answers = 0


    # Get user by username
    result = cur.execute("SELECT * FROM users where user_username = %s", [username])
    if result > 0:
        data = cur.fetchone()
        name = data['user_name']
        email = data['user_email']
        id = data['user_id']
        date = data['register_date']

    result = cur.execute("SELECT * FROM questions WHERE poster = %s", [username])
    if result > 0:
        no_questions = result

    result = cur.execute("SELECT * FROM answers WHERE author = %s", [username])
    if result > 0:
        no_answers = result

    return render_template('profile.html', name=name, email=email, id=id, date=date, no_questions=no_questions, no_answers=no_answers)


@app.route('/search',methods = ['GET','POST'])
def search():
    strin=request.form['search']
    results = []
    results2 = []
    results3 = []

    cur = mysql.connection.cursor()
    query  = "'%"+strin+"%'"

    no = cur.execute("SELECT * FROM questions WHERE statement LIKE "+query)
    for row in cur:
        results.append(row)
    no2 = cur.execute("SELECT * FROM users WHERE user_username LIKE"+query)

    for row in cur:
        results2.append(row)
    cur.close()

    return render_template("search.html",results=results,results2=results2,no2=no2,no=no)


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


# Insert new Data
@app.route('/adddata', methods=['GET', 'POST'])
@is_loggedin
def adddata():
    return render_template('adddata.html')


# Insert Player Class
class InsertPlayerForm(Form):
    NBA_ID = StringField('NBA ID', [validators.Length(min=1, max=280)])
    PersonID = StringField('Person ID', [validators.Length(min=1, max=280)])
    Player_Name = StringField('Player Name', [validators.Length(min=1, max=280)])
    Team_Name = StringField('Team Name', [validators.Length(min=1, max=280)])
    Age = StringField('Age', [validators.Length(min=1, max=280)])
    Height = StringField('Height', [validators.Length(min=1, max=280)])
    Weight = StringField('Weight', [validators.Length(min=1, max=280)])
    College = StringField('College', [validators.Length(min=1, max=280)])
    Is_Injured = StringField('Is the player injured? If yes press 1, if no press 0', [validators.Length(min=1, max=280)])
    Yearly_Salary = StringField('Yearly Salary', [validators.Length(min=1, max=280)])
    Years_Left_On_Contract = StringField('Years left on Current Contract', [validators.Length(min=1, max=280)])
    No_Of_Games_Played = StringField('Games played in this season', [validators.Length(min=1, max=280)])
    Total_Points = StringField('Total Points this season', [validators.Length(min=1, max=280)])
    Country = StringField('Country', [validators.Length(min=1, max=280)])
    Latest_Award = StringField('Latest Award won', [validators.Length(min=1, max=280)])
    Date_Of_Winning_Award = StringField('Date of winning Latest Award', [validators.Length(min=1, max=280)])
    Jersey_Number = StringField('Jersey Number', [validators.Length(min=1, max=280)])


# Add Player Data
@app.route('/adddata/insertplayer', methods=['GET', 'POST'])
@is_loggedin
def insertplayer():
    form = InsertPlayerForm(request.form)
    if request.method == 'POST' and form.validate():
        NBA_ID = form.NBA_ID.data
        PersonID = form.PersonID.data
        Player_Name = form.Player_Name.data
        Team_Name = form.Team_Name.data
        Age = form.Age.data
        Height = form.Height.data
        Weight = form.Weight.data
        College = form.College.data
        Is_Injured = form.Is_Injured.data
        Yearly_Salary = form.Yearly_Salary.data
        Years_Left_On_Contract = form.Years_Left_On_Contract.data
        No_Of_Games_Played = form.No_Of_Games_Played.data
        Total_Points = form.Total_Points.data
        Country = form.Country.data
        Latest_Award = form.Latest_Award.data
        Date_Of_Winning_Award = form.Date_Of_Winning_Award.data
        Jersey_Number = form.Jersey_Number.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO Player (NBA_ID, PersonID, Player_Name, Team_Name, Age, Height, Weight, College, Is_Injured, Yearly_Salary, Years_Left_On_Contract, No_Of_Games_Played, Total_Points, Country, Latest_Award, Date_Of_Winning_Award, Jersey_Number, Posted_By) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(NBA_ID, PersonID, Player_Name, Team_Name, Age, Height, Weight, College, Is_Injured, Yearly_Salary, Years_Left_On_Contract, No_Of_Games_Played, Total_Points, Country, Latest_Award, Date_Of_Winning_Award, Jersey_Number, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('Player Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertplayer.html', form=form)


# Insert Coach Class
class InsertCoachForm(Form):
    PersonID = StringField('Person ID', [validators.Length(min=1, max=280)])
    Name = StringField('Coach Name', [validators.Length(min=1, max=280)])
    TeamID = StringField('Team ID', [validators.Length(min=1, max=280)])

# Add Coach Data
@app.route('/adddata/insertcoach', methods=['GET', 'POST'])
@is_loggedin
def insertcoach():
    form = InsertCoachForm(request.form)
    if request.method == 'POST' and form.validate():
        PersonID = form.PersonID.data
        Name = form.Name.data
        TeamID = form.TeamID.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO Coach (PersonID, Name, TeamID, Posted_By) VALUES(%s, %s, %s, %s)",(PersonID, Name, TeamID, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('Coach Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertcoach.html', form=form)


# Insert Owner Class
class InsertOwnerForm(Form):
    PersonID = StringField('Person ID', [validators.Length(min=1, max=280)])
    Name = StringField('Owner Name', [validators.Length(min=1, max=280)])
    TeamID = StringField('Team ID', [validators.Length(min=1, max=280)])

# Add Owner Data
@app.route('/adddata/insertowner', methods=['GET', 'POST'])
@is_loggedin
def insertowner():
    form = InsertOwnerForm(request.form)
    if request.method == 'POST' and form.validate():
        PersonID = form.PersonID.data
        Name = form.Name.data
        TeamID = form.TeamID.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO Owner (PersonID, Name, TeamID, Posted_By) VALUES(%s, %s, %s, %s)",(PersonID, Name, TeamID, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('Coach Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertowner.html', form=form)

# Insert MVP Class
class InsertMVPForm(Form):
    NBA_ID = StringField('NBA ID', [validators.Length(min=1, max=280)])
    TeamID = StringField('Team ID', [validators.Length(min=1, max=280)])
    Year_Won = StringField('Year Won', [validators.Length(min=1, max=280)])


# Add MVP Data
@app.route('/adddata/insertmvp', methods=['GET', 'POST'])
@is_loggedin
def insertmvp():
    form = InsertMVPForm(request.form)
    if request.method == 'POST' and form.validate():
        NBA_ID = form.NBA_ID.data
        TeamID = form.TeamID.data
        Year_Won = form.Year_Won.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO MVP (NBA_ID, TeamID, Year_Won, Posted_By) VALUES(%s, %s, %s, %s)",(NBA_ID, TeamID, Year_Won, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('MVP Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertmvp.html', form=form)


# Insert DPOY Class
class InsertDPOYForm(Form):
    NBA_ID = StringField('NBA ID', [validators.Length(min=1, max=280)])
    TeamID = StringField('Team ID', [validators.Length(min=1, max=280)])
    Year_Won = StringField('Year Won', [validators.Length(min=1, max=280)])


# Add DPOY Data
@app.route('/adddata/insertdpoy', methods=['GET', 'POST'])
@is_loggedin
def insertdpoy():
    form = InsertDPOYForm(request.form)
    if request.method == 'POST' and form.validate():
        NBA_ID = form.NBA_ID.data
        TeamID = form.TeamID.data
        Year_Won = form.Year_Won.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO DPOY (NBA_ID, TeamID, Year_Won, Posted_By) VALUES(%s, %s, %s, %s)",(NBA_ID, TeamID, Year_Won, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('DPOY Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertdpoy.html', form=form)


# Insert Champion Class
class InsertChampionForm(Form):
    TeamID = StringField('Team ID', [validators.Length(min=1, max=280)])
    Year_Won = StringField('Year Won', [validators.Length(min=1, max=280)])
    Finals_MVP_NBA_ID = StringField('Finals MVP NBA ID', [validators.Length(min=1, max=280)])


# Add Champion Data
@app.route('/adddata/insertchampion', methods=['GET', 'POST'])
@is_loggedin
def insertchampion():
    form = InsertChampionForm(request.form)
    if request.method == 'POST' and form.validate():
        TeamID = form.TeamID.data
        Year_Won = form.Year_Won.data
        Finals_MVP_NBA_ID = form.Finals_MVP_NBA_ID.data
        
        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO Championship (TeamID, Year_Won, Finals_MVP_NBA_ID, Posted_By) VALUES(%s, %s, %s, %s)",(TeamID, Year_Won, Finals_MVP_NBA_ID, session['username']))

        mysql.connection.commit()
        cur.close()
        flash('Champion Inserted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('insertchampion.html', form=form)


@app.route('/alldata')
def alldata():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM Player")

    cur.execute("SELECT * FROM Player")
    qs = cur.fetchall()
    print(qs)

    if result > 0:
        return render_template('alldata.html', qs=qs)
    else:
        msg = "No Players found"
        return render_template('alldata.html',msg=msg)

    cur.close()

@app.route('/questions',defaults={'id':1})
@app.route('/questions/<int:id>/')
def question(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM questions ORDER BY id DESC")

    skip = (id-1)
    last = floor(result)

    if last == 0:
        last  = 1

    cur.execute("SELECT * FROM questions ORDER BY id DESC LIMIT %s,%s",(skip,1))
    qs = cur.fetchall()

    if id > last :
        return redirect(url_for('question',id = last))
    if result > 0:
        return render_template('questions.html',last=last, qs=qs,id=id)
    else:
        msg = "No questions found"
        return render_template('questions.html',msg=msg,id=id)

    cur.close()


@app.route('/questions/answered',defaults={'id':1})
@app.route('/questions/answered/<int:id>/')
def answered_question(id):
    answered = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions ORDER BY id DESC")

    for row in cur:
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT statement FROM answers,questions WHERE qid = %s",[row['id']])
        answered.append(cur2.fetchone())
        cur2.close()

    result = len(answered)
    skip = (id-1)
    last = floor(result)

    if last == 0:
        last  = 1

    cur.execute("SELECT * FROM answers ORDER BY qid DESC")
    qs = []

    previd = ""

    for row in cur:
        if previd != row['qid']:
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT * FROM questions WHERE id = %s LIMIT %s,%s",(row['qid'],skip,1))
            qs.append(cur2.fetchone())
            previd=row['qid']
            cur2.close()

    if id > last :
        return redirect(url_for('answered_question',id = last))
    if result > 0:
        return render_template('answered_questions.html',last=last, qs=qs,id=id,answered=answered)
    else:
        msg = "No questions found"
        return render_template('answered_questions.html',msg=msg,id=id,answered=answered)

    cur.close()


@app.route('/questions/unanswered',defaults={'id':1})
@app.route('/questions/unanswered/<int:id>/')
def unanswered_question(id):
    unanswered = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions ORDER BY id DESC")

    for row in cur:
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT statement FROM answers,questions WHERE qid != %s",[row['id']])
        unanswered.append(cur2.fetchone())
        cur2.close()

    result = len(unanswered)
    skip = (id-1)*1
    last = floor(result)

    if last == 0:
        last  = 1

    cur.execute("SELECT * FROM answers ORDER BY qid DESC")
    qs1 = []
    previd = ""

    for row in cur:
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM questions WHERE id != %s LIMIT %s,%s",(row['qid'],skip,1))
        qs1.append(cur2.fetchone())
        previd=row['qid']
        cur2.close()

    qs = list({v['id']:v for v in qs1}.values())

    if id > last :
        return redirect(url_for('unanswered_question',id = last))
    if result > 0:
        return render_template('unanswered_questions.html',last=last, qs=qs,id=id,unanswered=unanswered)
    else:
        msg = "No questions found"
        return render_template('unanswered_questions.html',msg=msg,id=id,unanswered=unanswered)

    cur.close()


@app.route('/editquestion/<string:id>',methods = ['GET','POST'])
@is_loggedin
def editquestion(id):
    cur2 = mysql.connection.cursor()

    result = cur2.execute("SELECT * FROM questions WHERE id = %s AND poster = %s",([id],[session['username']]))
    one_qs = cur2.fetchone()

    cur2.close()

    form = QuestionForm(request.form)
    form.statement.data = one_qs['statement']
    form.body.data = one_qs['body']

    if request.method == 'POST' and form.validate :
        body = request.form['body']
        statement = request.form['statement']

        cur=mysql.connection.cursor()

        cur.execute("UPDATE questions SET body=%s,statement=%s WHERE id = %s ",(body,statement,[id]))
        mysql.connection.commit()
        cur.close()

        flash ('Question Updated','success')
        return redirect(url_for('questions',id = id))
    return render_template('editquestion.html',form=form,one_qs=one_qs)


# Delete Player
@app.route('/delete_player/<string:id>', methods=['POST'])
@is_loggedin
def delete_player(id):
    # Create a cursor
    cur = mysql.connection.cursor()

    # Execute Cursor
    cur.execute("DELETE FROM Player where NBA_ID=%s", [id])

    mysql.connection.commit()
    cur.close()

    flash ('Player Deleted','success')
    return redirect(url_for('dashboard'))


@app.route('/delete_answer/<string:aid>/<int:qid>',methods=['GET','POST'])
@is_loggedin
def delete_answer(aid,qid):
    cur = mysql.connection.cursor()

    # Execute Cursor
    cur.execute("DELETE FROM answers where id=%s", [aid])

    mysql.connection.commit()
    cur.close()

    flash ('Answer Deleted','success')
    return redirect(url_for('questions',id = qid ))

# Comment form
class CommentForm(Form):
    body = TextAreaField('',[validators.Length(min=1,max=80)])


@app.route('/question/<string:id>/', methods=['GET', 'POST'])
def questions(id):
    cur = mysql.connection.cursor()

    if 'logged_in' not in session:
        username = None
        uid = 0
    else:
        username = session['username']
        cur.execute("SELECT * FROM users WHERE user_username = %s",[username])
        us = cur.fetchone()
        uid = us['user_id']

    cur.execute("SELECT * FROM questions WHERE id = %s",[id])
    one_qs = cur.fetchone()
    cur.close()

    cur = mysql.connection.cursor()
    auths = cur.execute("SELECT * FROM answers WHERE (author,qid) = (%s,%s)",([username],[id]))
    cur.close()

    cur2 = mysql.connection.cursor()

    result = cur2.execute("SELECT * FROM answers WHERE qid = %s ORDER BY upvote DESC",[id])
    answers = cur2.fetchall()

    cur2.close()

    comments = []

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM answers WHERE qid = %s ORDER BY upvote DESC",[id])

    for row in cur:
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM comments WHERE ansid = %s",[row['id']])
        comments.append(cur2.fetchall())
        cur2.close()

    cur.close()

    form1 = CommentForm(request.form)
    if request.method == 'POST':
        answerid = request.form['idd']
        if form1.validate() :
            body = form1.body.data
            cur3 = mysql.connection.cursor()
            cur3.execute("INSERT INTO comments(ansid,body,author) VALUES(%s, %s, %s)",([answerid],[body], session['username']))
            mysql.connection.commit()
            cur3.close()

            flash('Comment Posted', 'success')
            return redirect(url_for('questions',id=id))

    ups = 0
    if result > 0:
        return render_template('question.html',no_of_up=ups,uid=uid, form1=form1,one_qs=one_qs, answers=answers, username=username, auths=auths,comments=comments)
    else:
        msg = "Not Answered Yet"
        return render_template('question.html',no_of_up=ups,uid=uid, form1=form1,one_qs=one_qs, msg=msg, username=username, auths=auths,comments=comments)


<<<<<<< HEAD
@app.route('/upvote/<string:user_id>/<string:q_id>/<int:ans_id>/')
@is_loggedin
def upvote(user_id,q_id,ans_id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM answers WHERE id = %s",[ans_id])

    # if result == 0:
    #     abort(404)
    # post = cur.fetchone()
    result = cur.execute("SELECT * FROM votes WHERE userid = %s AND ansid = %s",([user_id],[ans_id]))
    cur.close()

    if result > 0:
        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM votes WHERE userid = %s AND ansid = %s",([user_id],[ans_id]))

        mysql.connection.commit()

        number = cur.execute("SELECT * FROM votes WHERE ansid = %s",[ans_id])

        cur.execute("UPDATE answers SET upvote = %s WHERE id = %s",(number,ans_id))

        mysql.connection.commit()

        cur.close()

        flash("Upvote Removed","danger")

        return redirect(url_for('questions',id=q_id))
    else :
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO votes(ansid,userid) VALUES(%s,%s)",([ans_id],[user_id]))

        mysql.connection.commit()

        number = cur.execute("SELECT * FROM votes WHERE ansid = %s",[ans_id])

        cur.execute("UPDATE answers SET upvote = %s WHERE id = %s",(number,ans_id))
        mysql.connection.commit()

        cur.close()

        flash("Upvoted","success")

        return redirect(url_for('questions',id=q_id))
    return redirect(url_for('questions',id=q_id))


=======
>>>>>>> 0bf8314c593bf35b269b92450916bc248cb017c4
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


@app.route('/editanswer/<string:id>',methods = ['GET','POST'])
@is_loggedin
def editanswer(id):
    form = AnswerForm(request.form)
    cur2 = mysql.connection.cursor()

    result = cur2.execute("SELECT * FROM questions WHERE id = %s",[id])
    one_qs = cur2.fetchone()

    cur2.close()


    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM answers WHERE qid = %s AND author = %s ",([id],[session['username']]))
    one_ans = cur.fetchone()

    form.body.data = one_ans['body']

    if request.method == 'POST' and form.validate :
        body = request.form['body']

        cur=mysql.connection.cursor()

        cur.execute("UPDATE answers SET body=%s WHERE author = %s",(body,session['username']))
        mysql.connection.commit()
        cur.close()

        flash ('Answer Updated','success')
        return redirect(url_for('question'))
    return render_template('editanswer.html',form=form,one_qs=one_qs)


# Running the app if app.py is the main module
if __name__ == '__main__':
    # Encryption Key
    app.secret_key='bZ\x85\xb2\xfc1$\xe6\n\xa1\xc0\xce\xdd\x9f\x815\xc0\xe4\xac\xc6\xfc\x0e\xa9\xa0V'

    # Starting the app
    app.run()
