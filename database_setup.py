import os
import sys
import pandas as pd
import mysql.connector
from mysql.connector import Error

from db_config import get_db_config, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def setup_database():
    print("=" * 65)
    print("  MYSQL 8.0 DATABASE MIGRATION & SETUP SCRIPT")
    print("=" * 65)
    print(f"Connecting to MySQL Server at {MYSQL_HOST}:{MYSQL_PORT} as '{MYSQL_USER}'...")

    try:
        # 1. Connect without selecting database to create database if not exists
        conn_server = mysql.connector.connect(**get_db_config(include_db=False))
        cursor_server = conn_server.cursor()
        
        print(f"Creating database '{MYSQL_DATABASE}' if not exists...")
        cursor_server.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        cursor_server.close()
        conn_server.close()
        print(f"[OK] Database '{MYSQL_DATABASE}' is ready.")

        # 2. Connect to the specific database
        conn = mysql.connector.connect(**get_db_config(include_db=True))
        cursor = conn.cursor()

        # Disable foreign key checks for clean table initialization
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # 3. Create Tables
        print("\nCreating/Verifying MySQL Tables...")

        # Table 1: students
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `students` (
                `Enrollment_No` VARCHAR(20) NOT NULL,
                `Name` VARCHAR(100) NOT NULL,
                `Phone_No` VARCHAR(25) NULL,
                `Email` VARCHAR(100) NULL,
                `Gender` VARCHAR(15) NULL,
                `Department` VARCHAR(100) NOT NULL,
                `Section` VARCHAR(10) NULL,
                `Semester` INT NULL,
                `Date_of_Birth` DATE NULL,
                `Address` TEXT NULL,
                `Academic_Year` VARCHAR(20) NULL,
                `CGPA` DECIMAL(4, 2) NULL,
                PRIMARY KEY (`Enrollment_No`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("  [OK] Table 'students' verified.")

        # Table 2: attendance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `attendance` (
                `Attendance_ID` INT AUTO_INCREMENT NOT NULL,
                `Enrollment_No` VARCHAR(20) NOT NULL,
                `Subject` VARCHAR(150) NOT NULL,
                `Attendance_Percentage` INT NOT NULL,
                PRIMARY KEY (`Attendance_ID`),
                INDEX `idx_att_enr` (`Enrollment_No`),
                CONSTRAINT `fk_att_student`
                    FOREIGN KEY (`Enrollment_No`) REFERENCES `students` (`Enrollment_No`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("  [OK] Table 'attendance' verified.")

        # Table 3: examination
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `examination` (
                `Exam_ID` INT AUTO_INCREMENT NOT NULL,
                `Enrollment_No` VARCHAR(20) NOT NULL,
                `Subject` VARCHAR(150) NOT NULL,
                `Internal_Marks` INT NOT NULL,
                `External_Marks` INT NOT NULL,
                `Total_Marks` INT NOT NULL,
                `Grade` VARCHAR(5) NOT NULL,
                PRIMARY KEY (`Exam_ID`),
                INDEX `idx_exam_enr` (`Enrollment_No`),
                CONSTRAINT `fk_exam_student`
                    FOREIGN KEY (`Enrollment_No`) REFERENCES `students` (`Enrollment_No`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("  [OK] Table 'examination' verified.")

        # Table 4: fees
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `fees` (
                `Fee_ID` INT AUTO_INCREMENT NOT NULL,
                `Enrollment_No` VARCHAR(20) NOT NULL,
                `Semester` INT NOT NULL,
                `Total_Fees` INT NOT NULL,
                `Paid_Amount` INT NOT NULL,
                `Pending_Amount` INT NOT NULL,
                `Payment_Status` VARCHAR(20) NOT NULL,
                PRIMARY KEY (`Fee_ID`),
                INDEX `idx_fees_enr` (`Enrollment_No`),
                CONSTRAINT `fk_fees_student`
                    FOREIGN KEY (`Enrollment_No`) REFERENCES `students` (`Enrollment_No`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        print("  [OK] Table 'fees' verified.")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # 4. Populate from CSV files idempotently
        print("\nMigrating CSV Data into MySQL Tables...")

        # Load CSVs
        students_df = pd.read_csv(os.path.join(DATA_DIR, "students.csv"))
        attendance_df = pd.read_csv(os.path.join(DATA_DIR, "attendance.csv"))
        examination_df = pd.read_csv(os.path.join(DATA_DIR, "examination.csv"))
        fees_df = pd.read_csv(os.path.join(DATA_DIR, "fees.csv"))

        # Truncate / Clear existing records to ensure idempotent fresh population without duplicates
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE `fees`;")
        cursor.execute("TRUNCATE TABLE `examination`;")
        cursor.execute("TRUNCATE TABLE `attendance`;")
        cursor.execute("TRUNCATE TABLE `students`;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # Insert Students
        sql_student = """
            INSERT INTO `students` (
                `Enrollment_No`, `Name`, `Phone_No`, `Email`, `Gender`, 
                `Department`, `Section`, `Semester`, `Date_of_Birth`, `Address`, 
                `Academic_Year`, `CGPA`
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        student_rows = [
            (
                row["Enrollment_No"], row["Name"], row["Phone_No"], row["Email"],
                row["Gender"], row["Department"], row["Section"], int(row["Semester"]),
                row["Date_of_Birth"], row["Address"], row["Academic_Year"], float(row["CGPA"])
            )
            for _, row in students_df.iterrows()
        ]
        cursor.executemany(sql_student, student_rows)
        print(f"  [INSERTED] {len(student_rows)} records into 'students'")

        # Insert Attendance
        sql_att = """
            INSERT INTO `attendance` (`Enrollment_No`, `Subject`, `Attendance_Percentage`)
            VALUES (%s, %s, %s);
        """
        att_rows = [
            (row["Enrollment_No"], row["Subject"], int(row["Attendance_Percentage"]))
            for _, row in attendance_df.iterrows()
        ]
        cursor.executemany(sql_att, att_rows)
        print(f"  [INSERTED] {len(att_rows)} records into 'attendance'")

        # Insert Examination
        sql_exam = """
            INSERT INTO `examination` (`Enrollment_No`, `Subject`, `Internal_Marks`, `External_Marks`, `Total_Marks`, `Grade`)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        exam_rows = [
            (row["Enrollment_No"], row["Subject"], int(row["Internal_Marks"]), int(row["External_Marks"]), int(row["Total_Marks"]), row["Grade"])
            for _, row in examination_df.iterrows()
        ]
        cursor.executemany(sql_exam, exam_rows)
        print(f"  [INSERTED] {len(exam_rows)} records into 'examination'")

        # Insert Fees
        sql_fees = """
            INSERT INTO `fees` (`Enrollment_No`, `Semester`, `Total_Fees`, `Paid_Amount`, `Pending_Amount`, `Payment_Status`)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        fees_rows = [
            (row["Enrollment_No"], int(row["Semester"]), int(row["Total_Fees"]), int(row["Paid_Amount"]), int(row["Pending_Amount"]), row["Payment_Status"])
            for _, row in fees_df.iterrows()
        ]
        cursor.executemany(sql_fees, fees_rows)
        print(f"  [INSERTED] {len(fees_rows)} records into 'fees'")

        conn.commit()

        # 5. Verify Row Counts in MySQL
        print("\nVerifying MySQL Data Counts:")
        for tbl in ["students", "attendance", "examination", "fees"]:
            cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            count = cursor.fetchone()[0]
            print(f"  - Table '{tbl}': {count} rows present in MySQL 8.0")

        cursor.close()
        conn.close()

        print("\n" + "=" * 65)
        print("  MIGRATION TO MYSQL 8.0 COMPLETED SUCCESSFULLY!")
        print("=" * 65)
        return True

    except Error as e:
        print("\n[ERROR] MySQL Migration Failed:", e)
        print("\nPlease ensure MySQL 8.0 Community Server is running and credentials in .env or environment variables are correct.")
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        sys.exit(1)
