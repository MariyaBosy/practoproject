from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from data import Articles
from flask_sqlalchemy import SQLAlchemy
import datetime
from functools import wraps
import pandas as pd
import csv
import os
from werkzeug.utils import secure_filename
import smtplib
import os
#Change this to use environment variables
EMAIL_ADDRESS = "quizapptesting@gmail.com"
EMAIL_PASSWORD = "practotest"


UPLOAD_FOLDER = 'csvfiles'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test1.db'
#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
#Use environment variables
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'quizapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#initialize MySQL
mysql = MySQL(app)
db = SQLAlchemy(app)

'''
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    def __repr__(self):
        return '<User %r>' % self.username
admin = User(username='admin', email='admin@example.com')
db.session.add(admin)
db.session.commit()
'''
class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	username = db.Column(db.String(100))
	college = db.Column(db.String(100))
	email = db.Column(db.String(100))
	password = db.Column(db.String(100))
	register_date = db.Column(db.Date, default = datetime.datetime.now())

class Questions(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	questionstring = db.Column(db.String(400))
	correctOptionNuumber = db.Column(db.Integer)
	difficultyLevel = db.Column(db.Integer)


@app.route('/')
def index():
	return render_template('home.html')
@app.route('/about')
def about():
	return render_template('about.html')


class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max = 25)])
	college = StringField('College', [validators.Length(min=6, max=50)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message = 'Passwords do not match')

		])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET', 'POST'])

def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		college = form.college.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		#Create cursor
		#cur = mysql.connection.cursor()

		#cur.execute("INSERT INTO students (name,username, college, email, password) values (%s, %s, %s,%s, %s )", (name, username, email,college, password))
		#mysql.connection.commit()
		student = Student(name = name, username = username, college = college, email = email, password = password)
		db.session.add(student)
		db.session.commit()
		#cur.close()
	
		flash('You are now registered and can log in ', 'success')

		return redirect(url_for('index'))


		#render_template('register.html')
	return render_template('register.html', form = form )


@app.route('/adminpanel', methods = ['GET'])

def displayadminpanel():
	print("Sender Email ID ->>",EMAIL_ADDRESS)
	return render_template('adminpanel.html')

@app.route('/adminpanel/questiontobank', methods=['GET'])

def renderAddQuestionToBank():
	return render_template('addquestiontobank.html')

@app.route('/adminpanel/questiontobank',methods=['POST'])
def addquestiontobank():
	data = request.form.to_dict()
	question = data['question']
	option1 = data['Option1']
	option2 = data['Option2']
	option3 = data['Option3']
	option4 = data['Option4']
	noofoptions=4
	if(data['Option5'] != ""):
		option5 = data['Option5']
		noofoptions = 5
	if(data['Option6'] != ""):
		option6 = data['Option6']
		noofoptions = noofoptions+1
	#Make sure noofoptions is greater than three
	correctoptionnumber = data['correct']
	difficulty = data['difficulty']
	if(int(correctoptionnumber) > noofoptions):
		flash('Check again','danger')
		return redirect(url_for('addquestiontobank'))
	quesObject = Questions(questionstring = question,correctOptionNuumber=correctoptionnumber, difficultyLevel = difficulty)
	db.session.add(quesObject)
	db.session.commit()
	#Validate that the correct option is always less than noofoptions


	
	
	flash('Question added ', 'success')
	
	return redirect('/adminpanel')
#Login
@app.route('/login',methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#Get form fields
		username = request.form['username']
		password_candidate = request.form['password']
		result = Student.query.filter_by(username=username).first()
		
		if result:
			#Get stored hash
			
			password = result.password

			if sha256_crypt.verify(password_candidate, password):
				app.logger.info("Password matched")
				#Passed
				session['logged_in'] = True
				session['username'] = username
				flash("You are now logged in ", 'success')
				#print("ITS WORKINGGG")
				return redirect(url_for('dashboard'))

			else:
				error = 'Invalid credentials'
				return render_template('login.html',error = error)
			cur.close()
			
		else:
			error = 'Username not found'
			return render_template('login.html',error = error)

	return render_template('login.html')


#Check if user logged in 

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, please log in ', 'danger')
			return redirect(url_for('login'))

	return wrap





@app.route('/logout')
def logout():
	session.clear()
	flash("You are now logged out", 'success')
	return redirect(url_for('login'))



@app.route('/dashboard')
@is_logged_in
def dashboard():
	return render_template('dashboard.html')

@app.route('/adminpanel/createtest',methods=['GET','POST'])

def createtest():
	if(request.method =='GET'):
		questions = Questions.query.all()
		return render_template('createtest.html', questions=questions)
	else:
		college = request.form.get("college")
		added_questions = []
		question_ids = db.session.query(Questions.id).all()
		question_id_list = [i[0] for i in question_ids]
		question_id_list_strings = [str(i) for i in question_id_list]
		for question_id in question_id_list_strings:
			if request.form.get(question_id,"off") == 'on':
				added_questions.append(int(question_id))
		
		
		msg = "Added questions "+ str(added_questions) + "for " + college 
		flash(msg,'success')
		return redirect(url_for('displayadminpanel'))
		
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/adminpanel/sendinvites',methods=['GET','POST'])
def sendinvites():
	if request.method == 'GET':
		return render_template('sendinvites.html')
	else:
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit an empty part without filename
		if file.filename == '':
			flash('No selected file','danger')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			emails = df.values[:,0] #List of emails from the file
			
			
			with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
				smtp.ehlo()
				smtp.starttls()
				smtp.ehlo()
				smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
				subject = 'Invitation for Practo test'
				body='You\'ve been invited to take a MCQ test'
				msg = f'Subject:{subject}\n\n{body}'
					
				for email in emails:
					smtp.sendmail(EMAIL_ADDRESS,email,msg)
					
				
			flash("Invites sent!", 'success')
			return redirect(url_for('displayadminpanel'))



	return "Done"




if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug = True)
