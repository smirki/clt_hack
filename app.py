from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import jsonify
from flask.helpers import redirect
from flask_mysqldb import MySQL
import mysql.connector
import openai
from flask_socketio import SocketIO, emit
 
# instance of flask application
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = 'some_secret_key'  # A secret key for Flask's session

# Initialize the OpenAI API with your token
openai.api_key = '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'

quiz_data = {
    'content': '',
    'num_questions': 0,
    'active': False,
    'students': {},  # Store student data by ID
    'custom_questions': []  # Initialize custom questions
}

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

    # Query the database to check for the suser's credentials
    query = "SELECT username, password, UserType FROM users_hack WHERE username = %s"
    cursor = mydb.cursor()
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    
    if user_data and user_data[1] == password:
        print(user_data)
        # Authentication successful
        userType = user_data[2]
        if userType == 'Teacher':
            return render_template('teacher.html', quiz_data=quiz_data)  #RENDER TEACHER DASHBOARD
        else:
             return render_template('index.html') #RENDER STUDENT DASHBOARD
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
               return render_template('teacher.html', quiz_data=quiz_data) #USE TEACHER DASHBOARD HERE
            else:
                return render_template('index.html') #USE STUDENT DASHBOARD HERE

    
@app.route('/create_exam')
def create_exam():
    return render_template('new_exam.html')
    


@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    global quiz_data
    if request.method == 'POST':
        # Capture custom questions and their answers if provided
        print("Form data received:", request.form)  # Diagnostic print
        custom_questions = request.form.getlist('custom_question[]')
        custom_answers = request.form.getlist('custom_answer[]')
        quiz_data['content'] = request.form.get('content', '')
        quiz_data['num_questions'] = int(request.form.get('num_questions', 0))
        quiz_data['custom_questions'] = list(zip(custom_questions, custom_answers))
        
        # Determine if we're on the Custom Questions tab or the Smart Questions tab
        tab_type = request.form.get('tab_type', 'smart')  # Default to "smart" if not provided
        
        if tab_type == 'smart' and not quiz_data['content']:
            print("Please provide content for smart questions before starting the quiz.", "error")
            return render_template('teacher.html', quiz_data=quiz_data)
        if tab_type == 'custom' and not quiz_data['custom_questions']:
            print("Please provide custom questions before starting the quiz.", "error")
            return render_template('teacher.html', quiz_data=quiz_data)
        
        
        
        if 'start' in request.form:
            quiz_data['active'] = True
            print("Quiz started successfully!", "success")
            # Check if there are custom questions. If yes, don't rely on OpenAI
            if custom_questions:
                quiz_data['use_openai'] = False
            else:
                quiz_data['use_openai'] = True
            
        if 'end' in request.form:
            quiz_data = {
                'content': '',
                'num_questions': 0,
                'active': False,
                'students': {},  # Store student data by ID
                'custom_questions': []  # Initialize custom questions
            }
            print("Quiz ended and data reset successfully!", "success")


        elif 'collect' in request.form:
            # For simplicity, just print reports to the console
            for student_id, answers in quiz_data['students'].items():
                report = generate_report(answers)
                print(f"Report for Student {student_id}: {report}")
            return redirect(url_for('teacher'))
    return render_template('teacher.html', quiz_data=quiz_data)



@app.route('/student/<id>', methods=['GET', 'POST'])
def student(id):
    if not quiz_data['active']:
        return "Quiz not active. Please wait for the teacher to start the quiz."
    
    if id not in quiz_data['students']:
        quiz_data['students'][id] = []
    
    if request.method == 'POST':
        answer = request.form['answer']
        question = request.form['question']
        print(answer)

        socketio.emit('student_update', {'student_id': id, 'results': quiz_data['students'][id]})
        
        if quiz_data['use_openai']:
            is_correct = check_answer(question, answer, quiz_data['content'])
        else:
            # Check if the answer matches the custom answer
            is_correct = any((q == question and a == answer) for q, a in quiz_data['custom_questions'])
        
        quiz_data['students'][id].append({'question': question, 'answer': answer, 'is_correct': is_correct})
        
        if len(quiz_data['students'][id]) < quiz_data['num_questions']:
            return redirect(url_for('student', id=id))
        else:
            return "Quiz completed. Thank you!"
    
    if quiz_data['use_openai']:
        if not quiz_data['content']:
            return "No content available for generating questions. Please contact the teacher."

        question = generate_open_ended_question(quiz_data['content'], quiz_data['students'][id])
    else:
        # Use one of the custom questions
        used_questions = [ans['question'] for ans in quiz_data['students'][id]]
        available_questions = [q for q, _ in quiz_data['custom_questions'] if q not in used_questions]
        question = available_questions[0] if available_questions else "No more questions available."
        if not available_questions:
            return "No more questions available. Please contact the teacher."
    return render_template('student.html', question=question)


def generate_open_ended_question(content, previous_answers):
    prompt = f"Create an open-ended question based on the following information: {content}"
    
    # Add context from previous answers if available
    if previous_answers:
        incorrect_answers = [ans for ans in previous_answers if not ans['is_correct']]
        if incorrect_answers:
            prompt += f" The student had difficulty with: {incorrect_answers[-1]['question']}"
    
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100
    )
    
    return response.choices[0].text.strip()


def check_answer(question, answer, context):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Is the following answer correct for the question? Context: {context}. Question: {question}. Answer: {answer}. Answer with yes or no.",
        max_tokens=10
    )

    print("HI", response.choices[0].text)
    
    response_text = response.choices[0].text.strip().lower()
    return 'yes' in response_text

def generate_report(all_answers):
    incorrect_questions = [ans['question'] for ans in all_answers if not ans['is_correct']]
    summary = f"The student had difficulty with the following questions: {'; '.join(incorrect_questions)}."

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Provide a detailed report based on the student's performance. {summary}",
        max_tokens=200
    )
    
    return response.choices[0].text.strip()

@app.route('/quiz_data', methods=['GET'])
def get_quiz_data():
    data = {
        "students": [],
        "num_questions": quiz_data['num_questions']
    }
    for student_id, answers in quiz_data['students'].items():
        correct_by_question = [ans['is_correct'] for ans in answers]
        data["students"].append({"student_id": student_id, "results": correct_by_question})
    return jsonify(data)

@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'username' not in session:
        return redirect(url_for('login_post'))

    if request.method == 'POST':
        # Handle form submission for importing content or taking quizzes
        # For now, let's just redirect to the student's quiz page
        student_id = session['username'] # assuming the username is unique and serves as an ID
        return redirect(url_for('student', id=student_id))
    
    return render_template('student_dashboard.html')


@app.route('/student_self_quiz', methods=['GET', 'POST'])
def student_self_quiz():
    if 'username' not in session or 'student_content' not in session or 'student_num_questions' not in session:
        return redirect(url_for('login_post'))

    content = session['student_content']
    num_questions = session['student_num_questions']

    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        is_correct = check_answer(question, answer, content)
        
        # Save the result (for now just print it, you can expand this)
        print(f"Question: {question}, Answer: {answer}, Correct: {is_correct}")

        if num_questions > 1:
            session['student_num_questions'] = num_questions - 1
            return redirect(url_for('student_self_quiz'))
        else:
            return "Quiz completed. Thank you!"
    
    question = generate_open_ended_question(content, [])
    return render_template('student.html', question=question)


@app.route('/student/<id>/report', methods=['GET'])
def student_report(id):
    if id in quiz_data['students']:
        report = generate_report(quiz_data['students'][id])
        return report
    return "No report available for this student."
 
if __name__ == '__main__':  
   app.run()