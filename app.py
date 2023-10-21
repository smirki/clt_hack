from flask import Flask,render_template, request
from flask_mysqldb import MySQL
import mysql.connector
 
# instance of flask application
app = Flask(__name__)


mydb = mysql.connector.connect(user='root', password='Soccersoccer23*', host='localhost', database='users_hack')
cursor = mydb.cursor()
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
    query = "SELECT username, password FROM users_hack WHERE username = %s"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    if user_data and user_data[1] == password:
        # Authentication successful
        return render_template('index.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    render_template('auth/signup.html')

     
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username or email already exists in the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users_hack WHERE username = %s OR email = %s", (username, email))
        user = cursor.fetchone()

        if user:
            flash('Username or email already exists. Please choose a different one.')
        else:
            cursor.execute("INSERT INTO users_hack (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
            mysql.connection.commit()
            flash('Registration successful. You can now log in.')
            return redirect(url_for('auth/login'))
    
    return render_template('login.html')





 
if __name__ == '__main__':  
   app.run()