from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from datetime import datetime
from attendance_taker import face_recognizer
from get_faces_from_camera_tkinter import Face_Register
from features_extraction_to_csv import FaceFeaturesExtractor
from flask import Flask, jsonify
import smtplib
from email.mime.text import MIMEText
from datetime import date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

attendance_taker_instance = None
get_faces_instance = None
Face_FeaturesExtractor_instance = None

face_recognizer_instance = face_recognizer()
Face_Register_instance = Face_Register
Face_FeaturesExtractor_instance = FaceFeaturesExtractor

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session['admin']:
            return redirect(url_for('login'))  # Redirect to login page if not logged in
        return func(*args, **kwargs)
    return decorated_function


def send_emails():
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect('attendance2.db')
        cursor = connection.cursor()

        # Get today's date
        today_date = date.today().strftime('%Y-%m-%d')

        print(today_date,"???????????????????/")

        # Execute the query
        query = """
            SELECT student.*
            FROM student
            LEFT JOIN attendance ON student.id = attendance.students_id AND attendance.date = '{today_date}'
            WHERE attendance.students_id IS NULL;

        """


        print(query,">>>>>>>>>>>>>>>>>>")

        cursor.execute(query)
        results = cursor.fetchall()

        # Close the database connection
        connection.close()

        # Email configuration
        sender_email = 'amulbabariya121@gmail.com'
        password = 'cbdwxzkyywwtpoxz'
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587


        print(results,"-------------------------")
    

     # Loop through the results and send emails
        for student_tuple in results:
        
            student = {
                'id': student_tuple[0],
                'name': student_tuple[1],
                'parents_email': student_tuple[2],
                # Add other columns as needed
            }
            recipient_email = student['parents_email']
            subject = 'Attendance Reminder'
            body = f"Dear {student['name']},\n\nThis is a reminder that you haven't attended any classes. Please attend the next session.\n\nSincerely,\nYour School"

            message = MIMEText(body)
            message['Subject'] = subject
            message['From'] = sender_email
            message['To'] = recipient_email

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, recipient_email, message.as_string())

            print("Doneeeeeeeeeeeeeeeeeeee")

        print(f"Email sent successfully to {recipient_email}")
        

    except Exception as e:
        print(e)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Add your admin authentication logic here
        # For example, if username and password match the admin credentials
        if username == 'admin' and password == '123456':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if 'admin' in session and session['admin']:
        # Render the admin dashboard template
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/send_emails', methods=['GET'])
@login_required
def route_send_emails():
    send_emails()
    return jsonify({"message": "Emails sent successfully."})

@app.route('/')
@login_required
def index():
    return render_template('index.html', selected_date='', no_data=False)



@app.route('/get_faces', methods=['GET'])
@login_required
def get_faces_route():
    get_faces_instance = Face_Register()
    get_faces_instance.run()
    return render_template('index.html')


@app.route('/attendance', methods=['POST'])
@login_required
def attendance():
    selected_date = request.form.get('selected_date')
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    formatted_date = selected_date_obj.strftime('%Y-%m-%d')

    print(formatted_date,">>>>>>>>>>>>>>>>>>>>>>>>>>")

    conn = sqlite3.connect('attendance2.db')
    cursor = conn.cursor()

    #cursor.execute("SELECT students_id,date, time, present FROM attendance WHERE date = ?", (formatted_date,))
    #attendance_data = cursor.fetchall()
    #print(attendance_data, "=============================")

    cursor.execute("SELECT * FROM student JOIN attendance ON student.id = attendance.students_id WHERE attendance.date = ?", (formatted_date,))
    all_data = cursor.fetchall()

    conn.close()

    if not all_data:
        return render_template('index.html', selected_date=selected_date, no_data=True, all_data=all_data)
    
    return render_template('index.html', selected_date=selected_date, attendance_data=all_data, all_data=all_data)

@app.route('/start_attendance_taker', methods=['GET'])
@login_required
def start_attendance_taker():
    face_recognizer_instance.run()
    return render_template('index.html')

@app.route('/features_extraction', methods=['GET'])
@login_required
def features_extraction_route():
    face_extractor_instance = FaceFeaturesExtractor()
    face_extractor_instance.main()
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)