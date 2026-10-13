import mysql.connector
from db_config import get_db_config

def update_emails():
    conn = mysql.connector.connect(**get_db_config(include_db=True))
    cursor = conn.cursor()
    
    cursor.execute("UPDATE `students` SET `Email` = REPLACE(`Email`, '@nitm.ac.in', '@ifheindia.org');")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows in MySQL students table.")
    
    cursor.execute("SELECT `Enrollment_No`, `Name`, `Email` FROM `students`;")
    rows = cursor.fetchall()
    print("\nVerified MySQL Student Emails:")
    for r in rows:
        print(f"  {r[0]}: {r[1]} -> {r[2]}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_emails()
