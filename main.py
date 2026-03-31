import cv2
import numpy as np
import face_recognition
import os
import sqlite3
from datetime import datetime

# ================== LOAD IMAGES ==================
path = 'images'
images = []
classNames = []

for file in os.listdir(path):
    img = cv2.imread(f'{path}/{file}')
    if img is not None:
        images.append(img)
        classNames.append(os.path.splitext(file)[0].upper())

# ================== ENCODING ==================
def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 0:
            encodeList.append(encodings[0])
    return encodeList

encodeListKnown = findEncodings(images)
print("Encodings Ready")

# ================== ATTENDANCE ==================
def markAttendance(name):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    now = datetime.now()
    time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')

    c.execute("INSERT INTO attendance VALUES (?, ?, ?)", (name, time, date))

    conn.commit()
    conn.close()

    print("Saved:", name)

# ================== CAMERA ==================
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

process_this_frame = True

# ================== MAIN LOOP ==================
while True:
    success, img = cap.read()
    if not success:
        break

    imgSmall = cv2.resize(img, (0, 0), None, 0.2, 0.2)
    imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

    faces = []
    encodes = []

    if process_this_frame:
        faces = face_recognition.face_locations(imgSmall)
        encodes = face_recognition.face_encodings(imgSmall, faces)

    process_this_frame = not process_this_frame

    # ================== RECOGNITION ==================
    for encodeFace, faceLoc in zip(encodes, faces):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        name = "UNKNOWN"
        color = (0, 0, 255)

        if len(faceDis) > 0:
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex] and faceDis[matchIndex] < 0.4:
                name = classNames[matchIndex].upper()
                color = (0, 255, 0)

                # ✅ ALWAYS SAVE (NO CONDITION)
                markAttendance(name)

        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1*5, x2*5, y2*5, x1*5

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, name, (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # ================== UI ==================
    current_time = datetime.now().strftime('%H:%M:%S')

    cv2.putText(img, "SMART ATTENDANCE SYSTEM", (20, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.putText(img, current_time, (480, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow('Smart Attendance', img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()