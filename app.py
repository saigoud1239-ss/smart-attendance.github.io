from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client  # 👈 ADD THIS

app = Flask(__name__)

# ================= TWILIO CONFIG =================
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP")

def send_whatsapp_alert(phone, student_name):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP,
            to=f"whatsapp:+91{phone}",   # +91 for India
            body=(
                f"⚠️ Attendance Alert!\n"
                f"Dear Parent, your ward *{student_name}* was marked "
                f"ABSENT on {datetime.now().strftime('%d-%m-%Y')}.\n"
                f"Please contact the college for more information."
            )
        )
        print(f"✅ WhatsApp sent to {phone}")
    except Exception as e:
        print(f"❌ WhatsApp failed: {e}")


# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        password = request.form['password']

        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=? AND password=?", (user_id, password))
        user = c.fetchone()
        conn.close()

        if user:
            return redirect(f"/dashboard/{user_id}")
        else:
            return "Invalid Login ❌"

    return render_template('login.html')


# ================= DASHBOARD =================
@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if user is None:
        return "User not found ❌"

    name = user[1]
    class_name = user[3]
    father = "Not Available"
    photo = "default.jpg"

    # ✅ Get phone from DB
    c.execute("SELECT phone FROM users WHERE id=?", (user_id,))
    phone_result = c.fetchone()
    phone = phone_result[0] if phone_result and phone_result[0] else "Not Available"

    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    # ================= TODAY SLOTS =================
    c.execute("SELECT time FROM attendance WHERE name=? AND date=?", (name, today))
    records = c.fetchall()

    times_today = [datetime.strptime(t[0], "%H:%M:%S") for t in records]

    slots = []
    labels = []

    for i in range(6):
        end = now - timedelta(minutes=i*5)
        start = end - timedelta(minutes=5)
        label = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        labels.append(label)

        found = any(
            start <= t.replace(year=now.year, month=now.month, day=now.day) <= end
            for t in times_today
        )
        slots.append(found)

    slots.reverse()
    labels.reverse()

    # ================= PERCENTAGE =================
    total_slots = len(slots)
    present_slots = sum(slots)
    percentage = round((present_slots / total_slots) * 100, 2) if total_slots > 0 else 0

    # ================= WHATSAPP ALERT =================
    last_slot_absent = not slots[-1]  # Most recent 5-min window

    if last_slot_absent and phone != "Not Available":
        send_whatsapp_alert(phone, name)

    # ================= SESSION HISTORY =================
    c.execute("SELECT date, time FROM attendance WHERE name=? ORDER BY date, time", (name,))
    data = c.fetchall()

    sessions = []
    current_session = []

    for i in range(len(data)):
        current_session.append(data[i])
        if i == len(data) - 1:
            sessions.append(current_session)
        else:
            t1 = datetime.strptime(data[i][1], "%H:%M:%S")
            t2 = datetime.strptime(data[i+1][1], "%H:%M:%S")
            if (t2 - t1).total_seconds() > 600:
                sessions.append(current_session)
                current_session = []

    session_tables = []
    for session in sessions:
        if not session:
            continue
        times = [datetime.strptime(s[1], "%H:%M:%S") for s in session]
        start_time = times[0]
        session_slots = []
        session_labels = []

        for i in range(6):
            start = start_time + timedelta(minutes=i*5)
            end = start + timedelta(minutes=5)
            label = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
            session_labels.append(label)
            found = any(start <= t <= end for t in times)
            session_slots.append(found)

        session_tables.append({"labels": session_labels, "slots": session_slots})

    conn.close()

    return render_template(
        'dashboard.html',
        name=name,
        roll=user[0],
        class_name=class_name,
        father=father,
        phone=phone,
        photo=photo,
        slots=slots,
        labels=labels,
        percentage=percentage,
        session_tables=session_tables
    )


# ================= EXPORT =================
@app.route('/export/<user_id>')
def export(user_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if user is None:
        return "User not found ❌"

    name = user[1]
    c.execute("SELECT * FROM attendance WHERE name=?", (name,))
    data = c.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=["Name", "Time", "Date"])
    file_name = f"{name}_attendance.xlsx"
    df.to_excel(file_name, index=False)

    return send_file(file_name, as_attachment=True)


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)