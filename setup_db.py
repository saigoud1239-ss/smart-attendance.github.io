import sqlite3

conn = sqlite3.connect('attendance.db')
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    class TEXT,
    phone TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS attendance (
    name TEXT,
    time TEXT,
    date TEXT
)""")

# Add your students (id, name, password, class, phone)
students = [
    ('25K91A6613','ASHISH','1234','CSM-A','9876543210'),
    ('25K91A6635','RAHUL','1234','CSM-A','9876543211'),
    ('25K91A6646','SANJAY','1234','CSM-A','9876543212'),
    ('25K91A6631','SRINIKETH','1234','CSM-A','9392399092'),
    ('25K91A6649','MURARI','1234','CSM-A','93923990234'),
]

c.executemany("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)", students)

conn.commit()
conn.close()
print("✅ Database ready! Tables created and students added.")
