from flask import Flask,render_template, request
from flask.helpers import redirect
from flask_mysqldb import MySQL
import mysql.connector
 
# instance of flask application
app = Flask(__name__)


mydb = mysql.connector.connect(user='root', password='Soccersoccer23*', host='localhost', database='users_hack')

# app.config['MYSQL_HOST'] = '127.0.0.1'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'Soccersoccer23*'
# app.config['MYSQL_DB'] = 'users_hack'
 
# mysql = MySQL(app)

@app.route("/")
def hello_world():
    return render_template('auth/login.html')
 


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    # Query the database to check for the user's credentials
    query = "SELECT username, password, UserType FROM users_hack WHERE username = %s"
    cursor = mydb.cursor()
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    
    if user_data and user_data[1] == password:
        print(user_data)
        # Authentication successful
        userType = user_data[2]
        if userType == 'Teacher':
            return render_template('Teacher_Dash.html')
        else:
             return render_template('index.html')
    return render_template('auth/login.html')
            

@app.route('/signup_page')
def go_signup():
    return render_template('auth/signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']  # Assuming you have a form field for user type

   

    # Check if the username already exists in the database
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM users_hack WHERE Username = %s", (username,))
        user = cursor.fetchone()

        if user:
            print('Username already exists. Please choose a different one.')
            return render_template('auth/signup.html')
        else:
            cursor.execute("INSERT INTO users_hack (Username, Password, UserType) VALUES (%s, %s, %s)", (username, password, user_type))
            mydb.commit()
            print('Registration successful. You can now log in.')
            if user_type == 'Teacher':
                return render_template('Teacher_Dash.html')
            else:
                return render_template('index.html')

    
    





 
if __name__ == '__main__':  
   app.run()