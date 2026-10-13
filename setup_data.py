import os

base_dir = r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support"
data_dir = os.path.join(base_dir, "data")
templates_dir = os.path.join(base_dir, "templates")
static_css_dir = os.path.join(base_dir, "static", "css")
static_js_dir = os.path.join(base_dir, "static", "js")

for d in [data_dir, templates_dir, static_css_dir, static_js_dir]:
    os.makedirs(d, exist_ok=True)

students_csv = """Enrollment_No,Name,Phone_No,Email,Gender,Department,Section,Semester,Date_of_Birth,Address,Academic_Year
2026CSE001,Aarav Sharma,+91 98765 43210,aarav.sharma@college.edu,Male,Computer Science & Engineering,A,6,2004-05-14,"102 Green Park, New Delhi",2023-2027
2026CSE002,Priya Patel,+91 98765 43211,priya.patel@college.edu,Female,Computer Science & Engineering,A,6,2004-08-22,"45 Sunrise Avenue, Ahmedabad",2023-2027
2026CSE003,Rohan Verma,+91 98765 43212,rohan.verma@college.edu,Male,Computer Science & Engineering,B,6,2003-11-30,"78 Lake View, Bhopal",2023-2027
2026CSE004,Sneha Reddy,+91 98765 43213,sneha.reddy@college.edu,Female,Computer Science & Engineering,B,6,2004-03-19,"12 Cyber Hills, Hyderabad",2023-2027
2026ECE001,Ananya Iyer,+91 98765 43214,ananya.iyer@college.edu,Female,Electronics & Communication Engineering,A,6,2004-01-10,"89 Temple Road, Chennai",2023-2027
2026ECE002,Vikram Singh,+91 98765 43215,vikram.singh@college.edu,Male,Electronics & Communication Engineering,A,6,2003-09-15,"23 Civil Lines, Jaipur",2023-2027
2026ECE003,Kavya Nair,+91 98765 43216,kavya.nair@college.edu,Female,Electronics & Communication Engineering,B,6,2004-07-04,"56 Palm Grove, Kochi",2023-2027
2026EEE001,Aditya Kulkarni,+91 98765 43217,aditya.kulkarni@college.edu,Male,Electrical & Electronics Engineering,A,6,2003-12-25,"14 Shivaji Marg, Pune",2023-2027
2026EEE002,Meera Das,+91 98765 43218,meera.das@college.edu,Female,Electrical & Electronics Engineering,A,6,2004-06-18,"67 Salt Lake, Kolkata",2023-2027
2026EEE003,Rahul Gupta,+91 98765 43219,rahul.gupta@college.edu,Male,Electrical & Electronics Engineering,B,6,2004-02-28,"31 Mall Road, Lucknow",2023-2027"""

attendance_csv = """Enrollment_No,Subject,Attendance_Percentage
2026CSE001,Data Warehousing & Mining,92
2026CSE001,Machine Learning,88
2026CSE001,Computer Networks,85
2026CSE001,Software Engineering,90
2026CSE002,Data Warehousing & Mining,95
2026CSE002,Machine Learning,94
2026CSE002,Computer Networks,91
2026CSE002,Software Engineering,96
2026CSE003,Data Warehousing & Mining,74
2026CSE003,Machine Learning,70
2026CSE003,Computer Networks,72
2026CSE003,Software Engineering,68
2026CSE004,Data Warehousing & Mining,89
2026CSE004,Machine Learning,85
2026CSE004,Computer Networks,87
2026CSE004,Software Engineering,91
2026ECE001,Digital Signal Processing,94
2026ECE001,VLSI Design,90
2026ECE001,Embedded Systems,92
2026ECE001,Wireless Communication,88
2026ECE002,Digital Signal Processing,78
2026ECE002,VLSI Design,82
2026ECE002,Embedded Systems,75
2026ECE002,Wireless Communication,80
2026ECE003,Digital Signal Processing,86
2026ECE003,VLSI Design,89
2026ECE003,Embedded Systems,84
2026ECE003,Wireless Communication,90
2026EEE001,Power System Analysis,88
2026EEE001,Control Systems,84
2026EEE001,Electrical Machines II,90
2026EEE001,Power Electronics,86
2026EEE002,Power System Analysis,96
2026EEE002,Control Systems,92
2026EEE002,Electrical Machines II,94
2026EEE002,Power Electronics,95
2026EEE003,Power System Analysis,72
2026EEE003,Control Systems,69
2026EEE003,Electrical Machines II,75
2026EEE003,Power Electronics,71"""

examination_csv = """Enrollment_No,Subject,Internal_Marks,External_Marks,Total_Marks,Grade
2026CSE001,Data Warehousing & Mining,28,62,90,A+
2026CSE001,Machine Learning,26,58,84,A
2026CSE001,Computer Networks,27,60,87,A
2026CSE001,Software Engineering,29,64,93,A+
2026CSE002,Data Warehousing & Mining,29,66,95,O
2026CSE002,Machine Learning,28,63,91,A+
2026CSE002,Computer Networks,27,62,89,A
2026CSE002,Software Engineering,30,67,97,O
2026CSE003,Data Warehousing & Mining,20,45,65,B
2026CSE003,Machine Learning,19,42,61,B
2026CSE003,Computer Networks,22,48,70,B+
2026CSE003,Software Engineering,18,40,58,C
2026CSE004,Data Warehousing & Mining,27,59,86,A
2026CSE004,Machine Learning,25,56,81,A
2026CSE004,Computer Networks,26,57,83,A
2026CSE004,Software Engineering,28,60,88,A
2026ECE001,Digital Signal Processing,28,64,92,A+
2026ECE001,VLSI Design,27,61,88,A
2026ECE001,Embedded Systems,29,63,92,A+
2026ECE001,Wireless Communication,26,59,85,A
2026ECE002,Digital Signal Processing,22,49,71,B+
2026ECE002,VLSI Design,24,52,76,B+
2026ECE002,Embedded Systems,21,47,68,B
2026ECE002,Wireless Communication,23,51,74,B+
2026ECE003,Digital Signal Processing,26,58,84,A
2026ECE003,VLSI Design,27,60,87,A
2026ECE003,Embedded Systems,25,56,81,A
2026ECE003,Wireless Communication,28,62,90,A+
2026EEE001,Power System Analysis,26,57,83,A
2026EEE001,Control Systems,25,55,80,A
2026EEE001,Electrical Machines II,27,60,87,A
2026EEE001,Power Electronics,26,58,84,A
2026EEE002,Power System Analysis,29,65,94,A+
2026EEE002,Control Systems,28,63,91,A+
2026EEE002,Electrical Machines II,29,64,93,A+
2026EEE002,Power Electronics,30,66,96,O
2026EEE003,Power System Analysis,20,44,64,B
2026EEE003,Control Systems,19,43,62,B
2026EEE003,Electrical Machines II,21,46,67,B
2026EEE003,Power Electronics,20,45,65,B"""

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

print("All 4 CSV files generated.")
