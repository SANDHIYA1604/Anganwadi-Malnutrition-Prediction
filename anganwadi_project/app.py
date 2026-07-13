from flask import Flask, render_template, request, redirect, session, url_for
import MySQLdb
import datetime
import joblib

app = Flask(__name__)
app.secret_key = "anganwadi_secret_key"

# Database connection
db = MySQLdb.connect(host="localhost", user="root", passwd="Sandhiya@1604", db="anganwadi_db")
risk_model = joblib.load('model/risk_model.pkl')

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user[0]
        session['role'] = user[4]
        return redirect(url_for('dashboard'))
    else:
        return "தவறான பயனர்பெயர் அல்லது கடவுச்சொல்! (Invalid username or password)"
@app.route('/add_child', methods=['GET', 'POST'])
def add_child():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        parent_name = request.form['parent_name']
        phone = request.form['phone']
        address = request.form['address']
        income_level = request.form['income_level']
        center_name = request.form['center_name']

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO children (name, dob, gender, parent_name, phone, address, income_level, center_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, dob, gender, parent_name, phone, address, income_level, center_name))
        db.commit()

        return "குழந்தை வெற்றிகரமாக பதிவு செய்யப்பட்டது! (Child registered successfully!) <br><a href='/add_child'>மேலும் ஒன்றைச் சேர்க்க</a> | <a href='/dashboard'>முகப்புக்குத் திரும்ப</a>"

    return render_template('add_child.html')
@app.route('/attendance')
def attendance_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    cursor = db.cursor()
    cursor.execute("SELECT child_id, name FROM children")
    children = cursor.fetchall()

    today = datetime.date.today().strftime('%d-%m-%Y')

    return render_template('attendance.html', children=children, today=today)


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    cursor = db.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')

    for key in request.form:
        if key.startswith('status_'):
            child_id = key.split('_')[1]
            status = request.form[key]
            cursor.execute("""
                INSERT INTO attendance (child_id, date, status)
                VALUES (%s, %s, %s)
            """, (child_id, today, status))

    db.commit()

    return "வருகை பதிவு செய்யப்பட்டது! (Attendance recorded!) <br><a href='/dashboard'>முகப்புக்குத் திரும்ப</a>"
@app.route('/health_entry')
def health_entry_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    cursor = db.cursor()
    cursor.execute("SELECT child_id, name FROM children")
    children = cursor.fetchall()

    return render_template('health_entry.html', children=children)


@app.route('/add_health_record', methods=['POST'])
def add_health_record():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    child_id = request.form['child_id']
    month = request.form['month']
    year = request.form['year']
    weight = request.form['weight']
    height = request.form['height']
    illness = request.form['illness']
    got_nutrition_food = request.form['got_nutrition_food']

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO health_records (child_id, month, year, weight, height, illness, got_nutrition_food)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (child_id, month, year, weight, height, illness, got_nutrition_food))
    db.commit()

    return "ஆரோக்கிய தகவல் சேமிக்கப்பட்டது! (Health record saved!) <br><a href='/health_entry'>மேலும் ஒன்றைச் சேர்க்க</a> | <a href='/dashboard'>முகப்புக்குத் திரும்ப</a>"
@app.route('/check_risk/<int:child_id>')
def check_risk(child_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    cursor = db.cursor()

    # Get child's name and DOB
    cursor.execute("SELECT name, dob FROM children WHERE child_id=%s", (child_id,))
    child = cursor.fetchone()
    child_name = child[0]
    dob = child[1]

    # Calculate age in months
    today = datetime.date.today()
    age_months = (today.year - dob.year) * 12 + (today.month - dob.month)

    # Get latest two weight records to calculate weight_change
    cursor.execute("""
        SELECT weight FROM health_records 
        WHERE child_id=%s 
        ORDER BY record_id DESC LIMIT 2
    """, (child_id,))
    weights = cursor.fetchall()

    if len(weights) < 2:
        weight_change = 0
    else:
        weight_change = weights[0][0] - weights[1][0]

    # Calculate attendance percentage
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE child_id=%s", (child_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE child_id=%s AND status='Present'", (child_id,))
    present = cursor.fetchone()[0]

    attendance_percent = (present / total * 100) if total > 0 else 100

    # Predict using AI model
    prediction = risk_model.predict([[weight_change, attendance_percent, age_months]])[0]

    risk_labels = {0: ("🟢 பாதுகாப்பானது (SAFE)", "green"),
                   1: ("🟡 கவனிக்க வேண்டியது (MODERATE RISK)", "orange"),
                   2: ("🔴 அதிக ஆபத்து (HIGH RISK)", "red")}

    risk_text, risk_color = risk_labels[prediction]

    # Save prediction to database
    cursor.execute("""
        INSERT INTO risk_predictions (child_id, date, risk_level)
        VALUES (%s, %s, %s)
    """, (child_id, today, risk_text))
    db.commit()

    return f"""
    <div style="text-align:center; font-family:sans-serif; margin-top:50px;">
        <h2>குழந்தை: {child_name}</h2>
        <p>எடை மாற்றம்: {weight_change} kg</p>
        <p>வருகை சதவீதம்: {attendance_percent:.1f}%</p>
        <h1 style="color:{risk_color};">{risk_text}</h1>
        <br>
        <a href="/dashboard">⬅ முகப்புப் பக்கம் (Back to Dashboard)</a>
    </div>
    """

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return f"Welcome to Dashboard! <br><a href='/add_child'>➕ Add New Child</a> | <a href='/attendance'>📋 Mark Attendance</a> | <a href='/health_entry'>⚖️ Health Entry</a> | <a href='/check_risk/1'>🤖 Check Risk (Test Child 1)</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)