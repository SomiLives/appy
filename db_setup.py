import mysql.connector
from config import MYSQL_CONFIG

conn = mysql.connector.connect(**MYSQL_CONFIG)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS lectures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    transcript TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database and tables created successfully.")
