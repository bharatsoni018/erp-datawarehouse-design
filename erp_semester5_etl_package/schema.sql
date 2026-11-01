-- ERP Semester 5 demonstration schema. Review database name before running.
CREATE DATABASE IF NOT EXISTS erp_datawarehouse;
USE erp_datawarehouse;

CREATE TABLE IF NOT EXISTS students (
 Enrollment_No VARCHAR(20) NOT NULL PRIMARY KEY, Name VARCHAR(100) NOT NULL, Phone_No VARCHAR(25) NULL, Email VARCHAR(100) NULL, Gender VARCHAR(15) NULL, Department VARCHAR(100) NOT NULL, Section VARCHAR(10) NULL, Semester INT NULL, Date_of_Birth DATE NULL, Address TEXT NULL, Academic_Year VARCHAR(20) NULL, CGPA DECIMAL(4,2) NULL
);
CREATE TABLE IF NOT EXISTS attendance (
 Attendance_ID INT AUTO_INCREMENT PRIMARY KEY, Enrollment_No VARCHAR(20) NOT NULL, Subject VARCHAR(150) NOT NULL, Attendance_Percentage INT NOT NULL, CONSTRAINT fk_attendance_student FOREIGN KEY (Enrollment_No) REFERENCES students(Enrollment_No) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS examination (
 Exam_ID INT AUTO_INCREMENT PRIMARY KEY, Enrollment_No VARCHAR(20) NOT NULL, Subject VARCHAR(150) NOT NULL, Internal_Marks INT NOT NULL, External_Marks INT NOT NULL, Total_Marks INT NOT NULL, Grade VARCHAR(5) NOT NULL, CONSTRAINT fk_examination_student FOREIGN KEY (Enrollment_No) REFERENCES students(Enrollment_No) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS fees (
 Fee_ID INT AUTO_INCREMENT PRIMARY KEY, Enrollment_No VARCHAR(20) NOT NULL, Semester INT NOT NULL, Total_Fees INT NOT NULL, Paid_Amount INT NOT NULL, Pending_Amount INT NOT NULL, Payment_Status VARCHAR(20) NOT NULL, CONSTRAINT fk_fees_student FOREIGN KEY (Enrollment_No) REFERENCES students(Enrollment_No) ON DELETE CASCADE ON UPDATE CASCADE
);

-- SAFETY: this file does not delete or truncate data. Import CSVs only into an empty/new demo database,
-- or use a dedicated merge script after checking Enrollment_No collisions. Do not run database_setup.py blindly.
