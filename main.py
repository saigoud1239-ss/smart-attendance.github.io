import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime

# ================== LOAD IMAGES ==================
path = 'images'
images = []
classNames = []

for person in os.listdir(path):
    person_path = os.path.join(path, person)

    if os.path.isdir(person_path):
        for img_name in os.listdir(person_path):

            if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(person_path, img_name)
                img = cv2.imread(img_path)

                if img is not None:
                    images.append(img)
                    classNames.append(person.upper())

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
present_students = set()
all_students = set(classNames)

def markAttendance(name):
    with open('attendance.csv', 'a+') as f:
        f.seek(0)
        data = f.readlines()
        nameList = [line.split(',')[0] for line in data]

        if name not in nameList:
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            f.write(f'{name},{date},{time},PRESENT\n')

def markabsentese(absent):
    with open('attendance.csv', 'a+') as f:
        f.seek(0)
        data = f.readlines()
        nameList = [line.split(',')[0] for line in data]

        if absent not in nameList:
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            f.write(f'{absent},{date},{time},ABSENT\n')

           

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

    # Resize for speed
    imgSmall = cv2.resize(img, (0, 0), None, 0.2, 0.2)
    imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

    faces = []
    encodes = []

    # Process alternate frames
    if process_this_frame:
        faces = face_recognition.face_locations(imgSmall, model="hog")
        encodes = face_recognition.face_encodings(imgSmall, faces)

    process_this_frame = not process_this_frame

    # ================== RECOGNITION ==================
    for encodeFace, faceLoc in zip(encodes, faces):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        name = "UNKNOWN"
        color = (0, 0, 255)  # Red for unknown

        if len(faceDis) > 0:
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex] and faceDis[matchIndex] < 0.5:
                name = classNames[matchIndex].upper()
                color = (0, 255, 0)  # Green for known
                

                present_students.add(name)
                markAttendance(name)

        # Scale face back
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1*5, x2*5, y2*5, x1*5

        # Draw box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Name + status
        cv2.putText(img, f'{name}', (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # ================== UI DISPLAY ==================
    now = datetime.now()
    current_time = now.strftime('%H:%M:%S')

    # Title
    cv2.putText(img, "SMART ATTENDANCE SYSTEM", (20, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # Time
    cv2.putText(img, current_time, (480, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Present count
    cv2.putText(img, f'Present: {len(present_students)}', (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show window
    cv2.imshow('Smart Attendance', img)

    # Exit on ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

# ================== FINAL OUTPUT ==================
absent_students = all_students - present_students
for absent in absent_students:
    markabsentese(absent) 

print("\nPresent Students:", present_students)
print("Absent Students:", absent_students)

cap.release()
cv2.destroyAllWindows()