import os

base_dir = r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support"
data_dir = os.path.join(base_dir, "data")

students_csv = """Enrollment_No,Name,Phone_No,Email,Gender,Department,Section,Semester,Date_of_Birth,Address,Academic_Year,CGPA
2026CSE001,Aarav Sharma,+91 98112 34501,aarav.sharma@college.edu,Male,Computer Science & Engineering,A,6,2004-05-14,"Flat 402, Green Valley Apts, Sector 62, Noida, UP - 201309",2023-2027,9.14
2026CSE002,Priya Patel,+91 98223 45602,priya.patel@college.edu,Female,Computer Science & Engineering,A,6,2004-08-22,"15 Shanti Niketan Society, Navrangpura, Ahmedabad, Gujarat - 380009",2023-2027,9.82
2026CSE003,Rohan Verma,+91 98334 56703,rohan.verma@college.edu,Male,Computer Science & Engineering,B,6,2003-11-30,"H-24, Arera Colony, Near Bittan Market, Bhopal, MP - 462016",2023-2027,6.45
2026CSE004,Sneha Reddy,+91 98445 67804,sneha.reddy@college.edu,Female,Computer Science & Engineering,B,6,2004-03-19,"Plot 88, Jubilee Hills, Road No. 36, Hyderabad, Telangana - 500033",2023-2027,8.55
2026ECE001,Ananya Iyer,+91 98556 78905,ananya.iyer@college.edu,Female,Electronics & Communication Engineering,A,6,2004-01-10,"12 Kasturba Nagar, 3rd Cross Street, Adyar, Chennai, TN - 600020",2023-2027,9.35
2026ECE002,Vikram Singh,+91 98667 89006,vikram.singh@college.edu,Male,Electronics & Communication Engineering,A,6,2003-09-15,"Bungalow 7, Civil Lines, Near Raj Mandir, Jaipur, Rajasthan - 302006",2023-2027,7.42
2026ECE003,Kavya Nair,+91 98778 90107,kavya.nair@college.edu,Female,Electronics & Communication Engineering,B,6,2004-07-04,"Villa 34, Palm Meadows, Panampilly Nagar, Kochi, Kerala - 682036",2023-2027,8.78
2026EEE001,Aditya Kulkarni,+91 98889 01208,aditya.kulkarni@college.edu,Male,Electrical & Electronics Engineering,A,6,2003-12-25,"42/B Mayur Colony, Kothrud, Pune, Maharashtra - 411038",2023-2027,8.20
2026EEE002,Meera Das,+91 98990 12309,meera.das@college.edu,Female,Electrical & Electronics Engineering,A,6,2004-06-18,"Block CD-120, Sector 1, Salt Lake City, Kolkata, WB - 700064",2023-2027,9.60
2026EEE003,Rahul Gupta,+91 98101 23410,rahul.gupta@college.edu,Male,Electrical & Electronics Engineering,B,6,2004-02-28,"18/45 Hazratganj, Park Road, Lucknow, UP - 226001",2023-2027,6.18"""

attendance_csv = """Enrollment_No,Subject,Attendance_Percentage
2026CSE001,Data Warehousing & Mining,92
2026CSE001,Machine Learning,89
2026CSE001,Computer Networks,94
2026CSE001,Cloud Computing,90
2026CSE001,Software Engineering,95
2026CSE002,Data Warehousing & Mining,96
2026CSE002,Machine Learning,98
2026CSE002,Computer Networks,95
2026CSE002,Cloud Computing,97
2026CSE002,Software Engineering,99
2026CSE003,Data Warehousing & Mining,68
2026CSE003,Machine Learning,64
2026CSE003,Computer Networks,72
2026CSE003,Cloud Computing,70
2026CSE003,Software Engineering,66
2026CSE004,Data Warehousing & Mining,88
2026CSE004,Machine Learning,85
2026CSE004,Computer Networks,90
2026CSE004,Cloud Computing,86
2026CSE004,Software Engineering,91
2026ECE001,Digital Signal Processing,95
2026ECE001,VLSI Design,92
2026ECE001,Embedded Systems,94
2026ECE001,Wireless Communication,90
2026ECE001,Microcontrollers & RTOS,96
2026ECE002,Digital Signal Processing,76
2026ECE002,VLSI Design,80
2026ECE002,Embedded Systems,74
2026ECE002,Wireless Communication,78
2026ECE002,Microcontrollers & RTOS,82
2026ECE003,Digital Signal Processing,89
2026ECE003,VLSI Design,91
2026ECE003,Embedded Systems,87
2026ECE003,Wireless Communication,92
2026ECE003,Microcontrollers & RTOS,88
2026EEE001,Power System Analysis,86
2026EEE001,Control Systems,84
2026EEE001,Electrical Machines II,89
2026EEE001,Power Electronics,85
2026EEE001,Renewable Energy Systems,90
2026EEE002,Power System Analysis,97
2026EEE002,Control Systems,94
2026EEE002,Electrical Machines II,96
2026EEE002,Power Electronics,98
2026EEE002,Renewable Energy Systems,95
2026EEE003,Power System Analysis,62
2026EEE003,Control Systems,58
2026EEE003,Electrical Machines II,65
2026EEE003,Power Electronics,60
2026EEE003,Renewable Energy Systems,64"""

examination_csv = """Enrollment_No,Subject,Internal_Marks,External_Marks,Total_Marks,Grade
2026CSE001,Data Warehousing & Mining,28,64,92,A+
2026CSE001,Machine Learning,27,62,89,A
2026CSE001,Computer Networks,29,66,95,O
2026CSE001,Cloud Computing,26,60,86,A
2026CSE001,Software Engineering,29,65,94,A+
2026CSE002,Data Warehousing & Mining,30,68,98,O
2026CSE002,Machine Learning,29,67,96,O
2026CSE002,Computer Networks,29,65,94,A+
2026CSE002,Cloud Computing,30,66,96,O
2026CSE002,Software Engineering,30,69,99,O
2026CSE003,Data Warehousing & Mining,18,42,60,B
2026CSE003,Machine Learning,16,38,54,C
2026CSE003,Computer Networks,20,46,66,B
2026CSE003,Cloud Computing,19,44,63,B
2026CSE003,Software Engineering,17,40,57,C
2026CSE004,Data Warehousing & Mining,26,58,84,A
2026CSE004,Machine Learning,25,57,82,A
2026CSE004,Computer Networks,27,60,87,A
2026CSE004,Cloud Computing,26,59,85,A
2026CSE004,Software Engineering,28,61,89,A
2026ECE001,Digital Signal Processing,29,64,93,A+
2026ECE001,VLSI Design,28,63,91,A+
2026ECE001,Embedded Systems,29,65,94,A+
2026ECE001,Wireless Communication,27,60,87,A
2026ECE001,Microcontrollers & RTOS,30,66,96,O
2026ECE002,Digital Signal Processing,22,48,70,B+
2026ECE002,VLSI Design,24,51,75,B+
2026ECE002,Embedded Systems,21,46,67,B
2026ECE002,Wireless Communication,23,49,72,B+
2026ECE002,Microcontrollers & RTOS,24,52,76,B+
2026ECE003,Digital Signal Processing,27,59,86,A
2026ECE003,VLSI Design,28,61,89,A
2026ECE003,Embedded Systems,26,58,84,A
2026ECE003,Wireless Communication,28,62,90,A+
2026ECE003,Microcontrollers & RTOS,27,60,87,A
2026EEE001,Power System Analysis,25,57,82,A
2026EEE001,Control Systems,24,55,79,B+
2026EEE001,Electrical Machines II,27,60,87,A
2026EEE001,Power Electronics,26,58,84,A
2026EEE001,Renewable Energy Systems,28,60,88,A
2026EEE002,Power System Analysis,30,66,96,O
2026EEE002,Control Systems,29,64,93,A+
2026EEE002,Electrical Machines II,29,65,94,A+
2026EEE002,Power Electronics,30,68,98,O
2026EEE002,Renewable Energy Systems,29,64,93,A+
2026EEE003,Power System Analysis,17,40,57,C
2026EEE003,Control Systems,15,36,51,D
2026EEE003,Electrical Machines II,18,43,61,B
2026EEE003,Power Electronics,16,39,55,C
2026EEE003,Renewable Energy Systems,18,41,59,C"""

fees_csv = """Enrollment_No,Semester,Total_Fees,Paid_Amount,Pending_Amount,Payment_Status
2026CSE001,6,85000,85000,0,Paid
2026CSE002,6,85000,85000,0,Paid
2026CSE003,6,85000,45000,40000,Partial
2026CSE004,6,85000,85000,0,Paid
2026ECE001,6,80000,80000,0,Paid
2026ECE002,6,80000,40000,40000,Partial
2026ECE003,6,80000,80000,0,Paid
2026EEE001,6,75000,75000,0,Paid
2026EEE002,6,75000,75000,0,Paid
2026EEE003,6,75000,0,75000,Pending"""

with open(os.path.join(data_dir, "students.csv"), "w", encoding="utf-8") as f:
    f.write(students_csv)
with open(os.path.join(data_dir, "attendance.csv"), "w", encoding="utf-8") as f:
    f.write(attendance_csv)
with open(os.path.join(data_dir, "examination.csv"), "w", encoding="utf-8") as f:
    f.write(examination_csv)
with open(os.path.join(data_dir, "fees.csv"), "w", encoding="utf-8") as f:
    f.write(fees_csv)

print("Updated 4 CSV datasets successfully.")
