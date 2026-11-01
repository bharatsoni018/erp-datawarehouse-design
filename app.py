import os
from io import BytesIO
from functools import wraps
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file

from db_config import DATA_MODE, get_db_config, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER
from data_store import get_store

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:  # MySQL is optional in CSV development mode.
    mysql = None
    Error = Exception

app = Flask(__name__)
# Generate fresh random secret key on application startup to ensure no stale sessions persist across restarts
app.secret_key = os.urandom(24).hex()
app.config["SESSION_PERMANENT"] = False

@app.after_request
def set_no_cache_headers(response):
    """Prevents browser from caching protected pages and Back-button navigation after logout."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ==========================================
# USER & ROLE ARCHITECTURE (FUTURE-READY)
# ==========================================
# Current version: ADMIN only.
# Future hierarchy: ADMIN -> HOD -> FACULTY -> STUDENTS.
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "Admin",
        "name": "Admin",
        "department": "ALL",
        "title": "Administrator"
    }
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access the Admin Portal.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# MYSQL 8.0 DATABASE ACCESS & INTEGRATION ENGINE
# ==========================================
def get_db_connection():
    """Establishes and returns an active MySQL 8.0 connection."""
    if DATA_MODE != "mysql":
        raise RuntimeError("MySQL access requested while DATA_MODE is not 'mysql'")
    if mysql is None:
        raise RuntimeError("mysql-connector-python is required when DATA_MODE=mysql")
    try:
        return mysql.connector.connect(**get_db_config(include_db=True))
    except Error as e:
        print(f"[FATAL] MySQL Connection Error: {e}")
        raise

def get_kpis():
    """Computes high-level Institutional KPIs dynamically from MySQL 8.0 tables."""
    if DATA_MODE == "csv":
        data = get_store()
        kpis = data.kpis()
        kpis.update({
            "departments_count": len(kpis["departments"]),
            "dept_counts": kpis["department_counts"],
            "avg_cgpa": round(float(data.students["CGPA"].mean()), 2),
            "total_fees": f"{kpis['total_fees']:,}",
            "total_paid": f"{kpis['total_paid']:,}",
            "total_pending": f"{kpis['total_pending']:,}",
            "subjects": sorted(data.attendance["Subject"].unique().tolist()),
        })
        return kpis
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Total students
    cursor.execute("SELECT COUNT(*) AS total FROM `students`;")
    total_students = cursor.fetchone()["total"]
    
    # 2. Department breakdown
    cursor.execute("SELECT `Department`, COUNT(*) AS `count` FROM `students` GROUP BY `Department`;")
    dept_counts = {row["Department"]: row["count"] for row in cursor.fetchall()}
    
    # 3. Average attendance across all records
    cursor.execute("SELECT AVG(`Attendance_Percentage`) AS `avg_att` FROM `attendance`;")
    avg_att_row = cursor.fetchone()["avg_att"]
    avg_attendance = round(float(avg_att_row), 1) if avg_att_row is not None else 0.0
    
    # 4. Average examination marks across all records
    cursor.execute("SELECT AVG(`Total_Marks`) AS `avg_marks` FROM `examination`;")
    avg_marks_row = cursor.fetchone()["avg_marks"]
    avg_marks = round(float(avg_marks_row), 1) if avg_marks_row is not None else 0.0
    
    # 5. Average CGPA across students
    cursor.execute("SELECT AVG(`CGPA`) AS `avg_cgpa` FROM `students`;")
    avg_cgpa_row = cursor.fetchone()["avg_cgpa"]
    avg_cgpa = round(float(avg_cgpa_row), 2) if avg_cgpa_row is not None else 0.0
    
    # 6. Fees summaries
    cursor.execute("SELECT SUM(`Total_Fees`) AS `total`, SUM(`Paid_Amount`) AS `paid`, SUM(`Pending_Amount`) AS `pending` FROM `fees`;")
    fee_totals = cursor.fetchone()
    total_fees = int(fee_totals["total"] or 0)
    total_paid = int(fee_totals["paid"] or 0)
    total_pending = int(fee_totals["pending"] or 0)
    
    # 7. Distinct filter lists
    cursor.execute("SELECT DISTINCT `Department` FROM `students` ORDER BY `Department`;")
    departments = [r["Department"] for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT `Section` FROM `students` ORDER BY `Section`;")
    sections = [r["Section"] for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT `Semester` FROM `students` ORDER BY `Semester`;")
    semesters = [int(r["Semester"]) for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT `Subject` FROM `attendance` ORDER BY `Subject`;")
    subjects = [r["Subject"] for r in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return {
        "total_students": total_students,
        "departments_count": len(departments),
        "dept_counts": dept_counts,
        "avg_attendance": avg_attendance,
        "avg_marks": avg_marks,
        "avg_cgpa": avg_cgpa,
        "total_fees": f"{total_fees:,}",
        "total_paid": f"{total_paid:,}",
        "total_pending": f"{total_pending:,}",
        "departments": departments,
        "sections": sections,
        "semesters": semesters,
        "subjects": subjects
    }

def get_integrated_student(enrollment_no):
    """
    Core Multi-Dataset Integration Engine:
    Finds matching records for the common Enrollment_No across 4 independent MySQL tables
    (students, attendance, examination, fees) and combines them into a single unified student profile.
    """
    if DATA_MODE == "csv":
        return get_store().student(enrollment_no)

    enrollment_no = enrollment_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Query Table 1: students (Personal Information)
    cursor.execute("SELECT * FROM `students` WHERE UPPER(`Enrollment_No`) = %s;", (enrollment_no,))
    student_row = cursor.fetchone()
    if not student_row:
        cursor.close()
        conn.close()
        return None
    
    # Format Date_of_Birth and CGPA
    if student_row.get("Date_of_Birth"):
        student_row["Date_of_Birth"] = str(student_row["Date_of_Birth"])
    if student_row.get("CGPA") is not None:
        student_row["CGPA"] = float(student_row["CGPA"])
        
    # 2. Query Table 2: attendance (Subject-wise Attendance Records)
    cursor.execute(
        "SELECT `Subject`, `Attendance_Percentage` FROM `attendance` WHERE UPPER(`Enrollment_No`) = %s ORDER BY `Attendance_ID`;", 
        (enrollment_no,)
    )
    attendance_records = cursor.fetchall()
    student_avg_att = round(sum(r["Attendance_Percentage"] for r in attendance_records) / len(attendance_records), 1) if attendance_records else 0
    
    # 3. Query Table 3: examination (Subject-wise Evaluation & Grades)
    cursor.execute(
        "SELECT `Subject`, `Internal_Marks`, `External_Marks`, `Total_Marks`, `Grade` FROM `examination` WHERE UPPER(`Enrollment_No`) = %s ORDER BY `Exam_ID`;", 
        (enrollment_no,)
    )
    exam_records = cursor.fetchall()
    student_avg_marks = round(sum(r["Total_Marks"] for r in exam_records) / len(exam_records), 1) if exam_records else 0
    
    # 4. Query Table 4: fees (Semester Billing & Payment Status)
    cursor.execute(
        "SELECT `Semester`, `Total_Fees`, `Paid_Amount`, `Pending_Amount`, `Payment_Status` FROM `fees` WHERE UPPER(`Enrollment_No`) = %s;", 
        (enrollment_no,)
    )
    fee_row = cursor.fetchone()
    if not fee_row:
        fee_row = {
            "Semester": student_row.get("Semester", "N/A"),
            "Total_Fees": 0,
            "Paid_Amount": 0,
            "Pending_Amount": 0,
            "Payment_Status": "Unknown"
        }
        
    cursor.close()
    conn.close()
    
    return {
        "personal": student_row,
        "attendance": {
            "records": attendance_records,
            "average": student_avg_att,
            "count": len(attendance_records)
        },
        "examination": {
            "records": exam_records,
            "average": student_avg_marks,
            "count": len(exam_records)
        },
        "fees": fee_row,
        "source_datasets": [
            {"name": "Dataset 1: Student Information", "file": "MySQL Table: students", "status": "Found"},
            {"name": "Dataset 2: Attendance Records", "file": "MySQL Table: attendance", "status": "Found"},
            {"name": "Dataset 3: Examination Results", "file": "MySQL Table: examination", "status": "Found"},
            {"name": "Dataset 4: Institutional Fees", "file": "MySQL Table: fees", "status": "Found"}
        ]
    }

# ==========================================
# AUTHENTICATION & LOGIN ROUTES
# ==========================================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = USERS.get(username)
        if user and user["password"] == password:
            session.clear()
            session["user"] = {
                "username": user["username"],
                "role": user["role"],
                "name": user["name"],
                "department": user["department"],
                "title": user["title"]
            }
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "danger")
            
    if "user" in session:
        return redirect(url_for("dashboard"))
        
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

# ==========================================
# APPLICATION ROUTES (MYSQL-POWERED)
# ==========================================

def get_dashboard_summary():
    """
    Computes consolidated high-level institutional summary metrics dynamically from MySQL.
    Strictly aggregates at student/institutional level without row inflation.
    """
    if DATA_MODE == "csv":
        data = get_store()
        students = data.students
        attendance = data.attendance.merge(
            students[["Enrollment_No", "Department"]], on="Enrollment_No", how="inner"
        )
        examination = data.examination
        fees = data.fees
        dept_attendance = attendance.groupby("Department")["Attendance_Percentage"].mean()
        student_attendance = attendance.groupby("Enrollment_No")["Attendance_Percentage"].mean()
        grades = examination["Grade"].value_counts()
        departments = []
        for department in sorted(students["Department"].unique()):
            dept_students = students[students["Department"] == department]
            dept_fees = fees[fees["Enrollment_No"].isin(dept_students["Enrollment_No"])]
            departments.append({
                "code": department,
                "name": department,
                "section": "Multiple",
                "students_count": len(dept_students),
                "avg_attendance": round(float(dept_attendance.get(department, 0)), 1),
                "semester": int(dept_students["Semester"].dropna().iloc[0]),
                "total_fees": int(dept_fees["Total_Fees"].sum()),
                "pending_fees": int(dept_fees["Pending_Amount"].sum()),
            })
        return {
            "student": {
                "total": len(students),
                "cse": int((students["Department"] == "CSE").sum()),
                "ece": int((students["Department"] == "ECE").sum()),
                "eee": int((students["Department"] == "EEE").sum()),
            },
            "attendance": {
                "overall_avg": round(float(attendance["Attendance_Percentage"].mean()), 1),
                "good_count": int((student_attendance >= 75).sum()),
                "low_count": int((student_attendance < 75).sum()),
                "cse_avg": round(float(dept_attendance.get("CSE", 0)), 1),
                "ece_avg": round(float(dept_attendance.get("ECE", 0)), 1),
                "eee_avg": round(float(dept_attendance.get("EEE", 0)), 1),
            },
            "examination": {
                "avg_marks": round(float(examination["Total_Marks"].mean()), 1),
                "highest_marks": int(examination["Total_Marks"].max()),
                "lowest_marks": int(examination["Total_Marks"].min()),
                "excellent_count": int(grades.get("O", 0) + grades.get("A+", 0)),
                "good_count": int(grades.get("A", 0) + grades.get("B+", 0)),
                "average_count": int(
                    grades.get("B", 0) + grades.get("C", 0)
                    + grades.get("D", 0) + grades.get("F", 0)
                ),
            },
            "fees": {
                "total": f"{int(fees['Total_Fees'].sum()):,}",
                "paid": f"{int(fees['Paid_Amount'].sum()):,}",
                "pending": f"{int(fees['Pending_Amount'].sum()):,}",
                "pending_students": int((fees["Pending_Amount"] > 0).sum()),
            },
            "departments": departments,
        }

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Student Summary
    cursor.execute("SELECT COUNT(*) AS total FROM `students`;")
    total_students = cursor.fetchone()["total"]
    
    cursor.execute("SELECT `Department`, COUNT(*) AS `count` FROM `students` GROUP BY `Department`;")
    dept_student_counts = {}
    for row in cursor.fetchall():
        dept_name = row["Department"]
        if "Computer Science" in dept_name or "CSE" in dept_name:
            dept_student_counts["CSE"] = row["count"]
        elif "Electronics & Communication" in dept_name or "ECE" in dept_name:
            dept_student_counts["ECE"] = row["count"]
        elif "Electrical" in dept_name or "EEE" in dept_name:
            dept_student_counts["EEE"] = row["count"]
            
    cse_count = dept_student_counts.get("CSE", 0)
    ece_count = dept_student_counts.get("ECE", 0)
    eee_count = dept_student_counts.get("EEE", 0)
    
    # 2. Attendance Summary
    cursor.execute("SELECT AVG(`Attendance_Percentage`) AS `avg_att` FROM `attendance`;")
    avg_att_row = cursor.fetchone()["avg_att"]
    overall_avg_att = round(float(avg_att_row), 1) if avg_att_row is not None else 0.0
    
    # Student-level attendance average (Good >= 75%, Low < 75%)
    cursor.execute("""
        SELECT a.`Enrollment_No`, AVG(a.`Attendance_Percentage`) AS `student_avg`, s.`Department`
        FROM `attendance` a
        JOIN `students` s ON a.`Enrollment_No` = s.`Enrollment_No`
        GROUP BY a.`Enrollment_No`, s.`Department`;
    """)
    student_att_records = cursor.fetchall()
    good_att_students = sum(1 for s in student_att_records if (s["student_avg"] or 0) >= 75)
    low_att_students = sum(1 for s in student_att_records if (s["student_avg"] or 0) < 75)
    
    # Department-wise Attendance
    cursor.execute("""
        SELECT s.`Department`, AVG(a.`Attendance_Percentage`) AS `dept_avg`
        FROM `attendance` a
        JOIN `students` s ON a.`Enrollment_No` = s.`Enrollment_No`
        GROUP BY s.`Department`;
    """)
    dept_att_dict = {}
    for r in cursor.fetchall():
        d_name = r["Department"]
        d_avg = round(float(r["dept_avg"]), 1) if r["dept_avg"] is not None else 0.0
        if "Computer Science" in d_name:
            dept_att_dict["CSE"] = d_avg
        elif "Electronics" in d_name and "Communication" in d_name:
            dept_att_dict["ECE"] = d_avg
        elif "Electrical" in d_name:
            dept_att_dict["EEE"] = d_avg
            
    # 3. Examination Summary
    cursor.execute("""
        SELECT AVG(`Total_Marks`) AS `avg_marks`, 
               MAX(`Total_Marks`) AS `max_marks`, 
               MIN(`Total_Marks`) AS `min_marks`
        FROM `examination`;
    """)
    exam_stats_row = cursor.fetchone()
    avg_marks = round(float(exam_stats_row["avg_marks"]), 1) if exam_stats_row and exam_stats_row["avg_marks"] is not None else 0.0
    highest_marks = int(exam_stats_row["max_marks"]) if exam_stats_row and exam_stats_row["max_marks"] is not None else 0
    lowest_marks = int(exam_stats_row["min_marks"]) if exam_stats_row and exam_stats_row["min_marks"] is not None else 0
    
    # Grade performance distribution
    cursor.execute("SELECT `Grade`, COUNT(*) AS `count` FROM `examination` GROUP BY `Grade`;")
    grades_map = {r["Grade"]: r["count"] for r in cursor.fetchall()}
    excellent_grades = grades_map.get("O", 0) + grades_map.get("A+", 0)
    good_grades = grades_map.get("A", 0) + grades_map.get("B+", 0)
    average_grades = grades_map.get("B", 0) + grades_map.get("C", 0) + grades_map.get("D", 0) + grades_map.get("F", 0)
    
    # 4. Fees & Payments Summary
    cursor.execute("""
        SELECT SUM(`Total_Fees`) AS `total_fees`, 
               SUM(`Paid_Amount`) AS `total_paid`, 
               SUM(`Pending_Amount`) AS `total_pending`,
               COUNT(CASE WHEN `Pending_Amount` > 0 OR `Payment_Status` != 'Paid' THEN 1 END) AS `pending_students`
        FROM `fees`;
    """)
    fee_row = cursor.fetchone()
    total_fees = int(fee_row["total_fees"] or 0)
    total_paid = int(fee_row["total_paid"] or 0)
    total_pending = int(fee_row["total_pending"] or 0)
    pending_students = int(fee_row["pending_students"] or 0)
    
    # 5. Department Overview Cards Data
    dept_overview = [
        {
            "code": "CSE",
            "name": "Computer Science & Engineering",
            "section": "A",
            "students_count": cse_count,
            "avg_attendance": dept_att_dict.get("CSE", 0.0),
            "semester": 6
        },
        {
            "code": "ECE",
            "name": "Electronics & Communication Engineering",
            "section": "B",
            "students_count": ece_count,
            "avg_attendance": dept_att_dict.get("ECE", 0.0),
            "semester": 6
        },
        {
            "code": "EEE",
            "name": "Electrical & Electronics Engineering",
            "section": "C",
            "students_count": eee_count,
            "avg_attendance": dept_att_dict.get("EEE", 0.0),
            "semester": 6
        }
    ]
    
    cursor.close()
    conn.close()
    
    return {
        "student": {
            "total": total_students,
            "cse": cse_count,
            "ece": ece_count,
            "eee": eee_count
        },
        "attendance": {
            "overall_avg": overall_avg_att,
            "good_count": good_att_students,
            "low_count": low_att_students,
            "cse_avg": dept_att_dict.get("CSE", 0.0),
            "ece_avg": dept_att_dict.get("ECE", 0.0),
            "eee_avg": dept_att_dict.get("EEE", 0.0)
        },
        "examination": {
            "avg_marks": avg_marks,
            "highest_marks": highest_marks,
            "lowest_marks": lowest_marks,
            "excellent_count": excellent_grades,
            "good_count": good_grades,
            "average_count": average_grades
        },
        "fees": {
            "total": f"{total_fees:,}",
            "paid": f"{total_paid:,}",
            "pending": f"{total_pending:,}",
            "pending_students": pending_students
        },
        "departments": dept_overview
    }


def _csv_module_data(kind, section_filter="", subject_filter="", status_filter="", search_q=""):
    data = get_store()
    students = data.students.copy()
    if search_q:
        q = search_q.lower()
        students = students[
            students["Enrollment_No"].str.lower().str.contains(q, na=False)
            | students["Name"].str.lower().str.contains(q, na=False)
        ]
    if section_filter:
        students = students[students["Section"].str.upper() == section_filter.upper()]
    ids = set(students["Enrollment_No"])
    frame = getattr(data, kind)
    frame = frame[frame["Enrollment_No"].isin(ids)].copy()
    if subject_filter and "Subject" in frame:
        frame = frame[frame["Subject"] == subject_filter]
    if status_filter and "Payment_Status" in frame:
        frame = frame[frame["Payment_Status"] == status_filter]
        if kind == "fees":
            students = students[students["Enrollment_No"].isin(frame["Enrollment_No"])]
    sections = []
    for section, section_students in students.groupby("Section", dropna=False, sort=True):
        items = []
        for enrollment_no, student in section_students.sort_values("Enrollment_No").set_index("Enrollment_No").iterrows():
            records = frame[frame["Enrollment_No"] == enrollment_no]
            student_data = student.to_dict()
            student_data["Enrollment_No"] = enrollment_no
            item = {
                "student": student_data,
                "section_letter": section or "Unknown",
                "semester": int(student["Semester"]) if pd.notna(student["Semester"]) else "Unknown",
                "records": records.to_dict("records"),
            }
            if kind == "attendance":
                item["average"] = round(float(records["Attendance_Percentage"].mean()), 1) if not records.empty else 0
            elif kind == "examination":
                item["average"] = round(float(records["Total_Marks"].mean()), 1) if not records.empty else 0
            else:
                item["fee"] = records.iloc[0].to_dict() if not records.empty else None
            items.append(item)
        if items:
            sections.append({
                "letter": section or "Unknown",
                "dept_code": "Multiple",
                "dept_name": "Section " + str(section or "Unknown"),
                "students": items,
                "student_count": len(items),
            })
    return students, frame, sections


def _paginate_sections(sections, page, page_size):
    """Paginate student cards while preserving their section grouping."""
    all_items = [(section, item) for section in sections for item in section["students"]]
    total = len(all_items)
    start = (page - 1) * page_size
    selected = all_items[start:start + page_size]
    grouped = {}
    for section, item in selected:
        grouped.setdefault(section["letter"], {**section, "students": []})
        grouped[section["letter"]]["students"].append(item)
    for section in grouped.values():
        section["student_count"] = len(section["students"])
    return list(grouped.values()), total

@app.route("/dashboard")
@login_required
def dashboard():
    """Consolidated institutional dashboard summary (No recent searches or detail tables)."""
    kpis = get_kpis()
    summary = get_dashboard_summary()
    return render_template("dashboard.html", kpis=kpis, summary=summary, active_page="dashboard")

@app.route("/search")
@login_required
def search():
    """Handles enrollment number search from search boxes."""
    enrollment_no = request.args.get("enrollment_no", "").strip()
    if not enrollment_no:
        flash("Please enter an Enrollment Number to search.", "warning")
        return redirect(url_for("search_student_page"))
    
    student = get_integrated_student(enrollment_no)
    if not student:
        flash(f"No student record found matching Enrollment Number '{enrollment_no}'.", "danger")
        return redirect(url_for("search_student_page"))
    
    matched_enr = student["personal"]["Enrollment_No"]
    return redirect(url_for("student_profile", enrollment_no=matched_enr))

@app.route("/search-student")
@login_required
def search_student_page():
    """Dedicated Search Student page."""
    example_students = []
    if DATA_MODE == "csv":
        example_students = get_store().students.head(4).to_dict("records")
    return render_template(
        "search_student.html",
        example_students=example_students,
        active_page="search_student",
    )

@app.route("/student/")
@login_required
def student_profile_index():
    """Report an incomplete profile URL instead of opening a general view."""
    return render_template(
        "student_error.html",
        error_title="Enrollment number required",
        error_message="A student profile URL must include an Enrollment_No.",
        error_code=400,
        active_page="students",
    ), 400

@app.route("/student/<enrollment_no>")
@login_required
def student_profile(enrollment_no):
    """Displays the unified student profile integrated across all 4 MySQL tables."""
    student_data = get_integrated_student(enrollment_no)
    if not student_data:
        return render_template(
            "student_error.html",
            error_title="Student not found",
            error_message=f"No student record exists for Enrollment_No '{enrollment_no}'.",
            error_code=404,
            active_page="students",
        ), 404
    
    return render_template(
        "profile.html",
        data=student_data,
        active_page="students"
    )

@app.route("/students")
@login_required
def students_page():
    """Student Management -> All Students Page (Queried from MySQL students table)."""
    kpis = get_kpis()

    dept_filter = request.args.get("department", "").strip()
    sec_filter = request.args.get("section", "").strip()
    sem_filter = request.args.get("semester", "").strip()
    search_q = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    page_size = min(max(request.args.get("page_size", 50, type=int), 1), 200)

    if DATA_MODE == "csv":
        students = get_store().students.copy()
        if dept_filter:
            students = students[students["Department"] == dept_filter]
        if sec_filter:
            students = students[students["Section"] == sec_filter]
        if sem_filter and sem_filter.isdigit():
            students = students[students["Semester"] == int(sem_filter)]
        if search_q:
            query = search_q.lower()
            students = students[
                students["Enrollment_No"].str.lower().str.contains(query, na=False)
                | students["Name"].str.lower().str.contains(query, na=False)
            ]
        students = students.sort_values("Enrollment_No")
        total_students = len(students)
        student_list = students.iloc[(page - 1) * page_size:page * page_size].to_dict("records")
        return render_template(
            "students.html",
            students=student_list,
            kpis=kpis,
            selected_dept=dept_filter,
            selected_sec=sec_filter,
            selected_sem=sem_filter,
            search_query=search_q,
            page=page,
            page_size=page_size,
            total_students=total_students,
            active_page="students",
        )

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM `students` WHERE 1=1"
    params = []
    
    if dept_filter:
        query += " AND `Department` = %s"
        params.append(dept_filter)
    if sec_filter:
        query += " AND `Section` = %s"
        params.append(sec_filter)
    if sem_filter and sem_filter.isdigit():
        query += " AND `Semester` = %s"
        params.append(int(sem_filter))
    if search_q:
        query += " AND (LOWER(`Enrollment_No`) LIKE %s OR LOWER(`Name`) LIKE %s)"
        params.append(f"%{search_q.lower()}%")
        params.append(f"%{search_q.lower()}%")
        
    query += " ORDER BY `Enrollment_No`;"
    cursor.execute(query, tuple(params))
    student_list = cursor.fetchall()
    for s in student_list:
        if s.get("Date_of_Birth"):
            s["Date_of_Birth"] = str(s["Date_of_Birth"])
        if s.get("CGPA") is not None:
            s["CGPA"] = float(s["CGPA"])
            
    cursor.close()
    conn.close()
    
    return render_template(
        "students.html",
        students=student_list,
        kpis=kpis,
        selected_dept=dept_filter,
        selected_sec=sec_filter,
        selected_sem=sem_filter,
        search_query=search_q,
        page=1,
        page_size=len(student_list) or 50,
        total_students=len(student_list),
        active_page="students"
    )

def map_student_to_section(student):
    """
    Strict Section mapping according to Department:
      CSE -> Section A
      ECE -> Section B
      EEE -> Section C
    """
    dept = (student.get("Department") or "").strip()
    enr = (student.get("Enrollment_No") or "").strip().upper()
    if enr.startswith("2026CSE") or "Computer Science" in dept or dept == "CSE":
        return "A"
    elif enr.startswith("2026ECE") or "Electronics & Communication" in dept or "Electronics and Communication" in dept or dept == "ECE":
        return "B"
    elif enr.startswith("2026EEE") or "Electrical" in dept or dept == "EEE":
        return "C"
    return "A"

@app.route("/attendance")
@login_required
def attendance_page():
    """
    Attendance Module:
    Exact hierarchy:
      SECTION A — Computer Science and Engineering (CSE) -> 4 CSE Students -> Subject-wise Attendance
      SECTION B — Electronics and Communication Engineering (ECE) -> 3 ECE Students -> Subject-wise Attendance
      SECTION C — Electrical and Electronics Engineering (EEE) -> 3 EEE Students -> Subject-wise Attendance
    Semester: Always Semester 6
    """
    kpis = get_kpis()
    sec_filter = request.args.get("section", "").strip().upper()
    subj_filter = request.args.get("subject", "").strip()
    search_q = request.args.get("q", "").strip()

    if DATA_MODE == "csv":
        students_list, flat_records, sections_data = _csv_module_data(
            "attendance", sec_filter, subj_filter, search_q=search_q
        )
        page = max(request.args.get("page", 1, type=int), 1)
        page_size = min(max(request.args.get("page_size", 10, type=int), 1), 100)
        sections_data, total_students = _paginate_sections(sections_data, page, page_size)
        values = flat_records["Attendance_Percentage"] if not flat_records.empty else pd.Series(dtype=float)
        student_avgs = flat_records.groupby("Enrollment_No")["Attendance_Percentage"].mean()
        return render_template(
            "attendance.html",
            sections_data=sections_data,
            summary_stats={
                "overall_avg": round(float(values.mean()), 1) if not values.empty else 0,
                "total_students": total_students,
                "low_attendance_count": int((student_avgs < 75).sum()),
            },
            records=flat_records.to_dict("records"),
            kpis=get_kpis(),
            selected_sec=sec_filter,
            selected_subj=subj_filter,
            search_query=search_q,
            page=page,
            page_size=page_size,
            total_students=total_students,
            active_page="attendance",
        )
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all students (or filtered by search query)
    student_query = "SELECT * FROM `students` WHERE 1=1"
    student_params = []
    if search_q:
        student_query += " AND (`Name` LIKE %s OR `Enrollment_No` LIKE %s)"
        student_params.extend([f"%{search_q}%", f"%{search_q}%"])
    student_query += " ORDER BY `Enrollment_No`;"
    cursor.execute(student_query, tuple(student_params))
    students_list = cursor.fetchall()
    
    # Fetch attendance records
    att_query = "SELECT a.`Enrollment_No`, a.`Subject`, a.`Attendance_Percentage`, a.`Attendance_ID`, s.`Name`, s.`Department` FROM `attendance` a LEFT JOIN `students` s ON a.`Enrollment_No` = s.`Enrollment_No` WHERE 1=1"
    att_params = []
    if subj_filter:
        att_query += " AND a.`Subject` = %s"
        att_params.append(subj_filter)
    if search_q:
        att_query += " AND (s.`Name` LIKE %s OR a.`Enrollment_No` LIKE %s)"
        att_params.extend([f"%{search_q}%", f"%{search_q}%"])
    att_query += " ORDER BY a.`Enrollment_No`, a.`Attendance_ID`;"
    cursor.execute(att_query, tuple(att_params))
    flat_records = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Map attendance by enrollment_no
    student_att_map = {}
    for att in flat_records:
        enr = att["Enrollment_No"]
        if enr not in student_att_map:
            student_att_map[enr] = []
        student_att_map[enr].append(att)
        
    # The 3 canonical sections as strictly mapped:
    # Section A = CSE, Section B = ECE, Section C = EEE
    sections_config = [
        {
            "letter": "A",
            "dept_code": "CSE",
            "dept_name": "Computer Science and Engineering (CSE)"
        },
        {
            "letter": "B",
            "dept_code": "ECE",
            "dept_name": "Electronics and Communication Engineering (ECE)"
        },
        {
            "letter": "C",
            "dept_code": "EEE",
            "dept_name": "Electrical and Electronics Engineering (EEE)"
        }
    ]
    
    sections_data = []
    all_att_percentages = []
    low_att_students_count = 0
    total_displayed_students = 0
    
    for sec in sections_config:
        # If user selected a specific section filter, filter accordingly
        if sec_filter and sec_filter not in [sec["letter"], sec["dept_code"]]:
            continue
            
        sec_students = [s for s in students_list if map_student_to_section(s) == sec["letter"]]
        student_items = []
        
        for s in sec_students:
            enr = s["Enrollment_No"]
            records = student_att_map.get(enr, [])
            
            # If subject filter is active, only include if they have matching records
            if subj_filter and not records:
                continue
                
            avg_att = round(sum(r["Attendance_Percentage"] for r in records) / len(records), 1) if records else 0
            if records:
                all_att_percentages.extend([r["Attendance_Percentage"] for r in records])
                
            if avg_att < 75:
                low_att_students_count += 1
                
            student_items.append({
                "student": s,
                "section_letter": sec["letter"],
                "semester": 6,
                "records": records,
                "average": avg_att
            })
            total_displayed_students += 1
            
        # Add section if there are students
        if student_items or (not search_q and not subj_filter):
            sections_data.append({
                "letter": sec["letter"],
                "dept_code": sec["dept_code"],
                "dept_name": sec["dept_name"],
                "students": student_items,
                "student_count": len(student_items)
            })
            
    overall_avg_att = round(sum(all_att_percentages) / len(all_att_percentages), 1) if all_att_percentages else 0
    
    summary_stats = {
        "overall_avg": overall_avg_att,
        "total_students": total_displayed_students,
        "low_attendance_count": low_att_students_count
    }
    
    return render_template(
        "attendance.html",
        sections_data=sections_data,
        summary_stats=summary_stats,
        records=flat_records,
        kpis=kpis,
        selected_sec=sec_filter,
        selected_subj=subj_filter,
        search_query=search_q,
        active_page="attendance"
    )

@app.route("/examination")
@login_required
def examination_page():
    """
    Examination Module:
    Exact hierarchy:
      SECTION A — Computer Science and Engineering (CSE) -> 4 CSE Students -> Subject-wise Examination
      SECTION B — Electronics and Communication Engineering (ECE) -> 3 ECE Students -> Subject-wise Examination
      SECTION C — Electrical and Electronics Engineering (EEE) -> 3 EEE Students -> Subject-wise Examination
    Semester: Always Semester 6
    """
    kpis = get_kpis()
    sec_filter = request.args.get("section", "").strip().upper()
    subj_filter = request.args.get("subject", "").strip()
    search_q = request.args.get("q", "").strip()

    if DATA_MODE == "csv":
        students_list, flat_records, sections_data = _csv_module_data(
            "examination", sec_filter, subj_filter, search_q=search_q
        )
        page = max(request.args.get("page", 1, type=int), 1)
        page_size = min(max(request.args.get("page_size", 10, type=int), 1), 100)
        sections_data, total_students = _paginate_sections(sections_data, page, page_size)
        values = flat_records["Total_Marks"] if not flat_records.empty else pd.Series(dtype=float)
        return render_template(
            "examination.html",
            sections_data=sections_data,
            summary_stats={
                "overall_avg": round(float(values.mean()), 1) if not values.empty else 0,
                "highest_marks": int(values.max()) if not values.empty else 0,
                "subjects_count": int(flat_records["Subject"].nunique()) if not flat_records.empty else 0,
                "total_students": total_students,
            },
            records=flat_records.to_dict("records"),
            kpis=get_kpis(),
            selected_sec=sec_filter,
            selected_subj=subj_filter,
            search_query=search_q,
            page=page,
            page_size=page_size,
            total_students=total_students,
            active_page="examination",
        )
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all students (or filtered by search query)
    student_query = "SELECT * FROM `students` WHERE 1=1"
    student_params = []
    if search_q:
        student_query += " AND (`Name` LIKE %s OR `Enrollment_No` LIKE %s)"
        student_params.extend([f"%{search_q}%", f"%{search_q}%"])
    student_query += " ORDER BY `Enrollment_No`;"
    cursor.execute(student_query, tuple(student_params))
    students_list = cursor.fetchall()
    
    # Fetch examination records
    exam_query = """
        SELECT e.`Enrollment_No`, e.`Subject`, e.`Internal_Marks`, e.`External_Marks`, 
               e.`Total_Marks`, e.`Grade`, e.`Exam_ID`, s.`Name`, s.`Department` 
        FROM `examination` e 
        LEFT JOIN `students` s ON e.`Enrollment_No` = s.`Enrollment_No` 
        WHERE 1=1
    """
    exam_params = []
    if subj_filter:
        exam_query += " AND e.`Subject` = %s"
        exam_params.append(subj_filter)
    if search_q:
        exam_query += " AND (s.`Name` LIKE %s OR e.`Enrollment_No` LIKE %s)"
        exam_params.extend([f"%{search_q}%", f"%{search_q}%"])
    exam_query += " ORDER BY e.`Enrollment_No`, e.`Exam_ID`;"
    cursor.execute(exam_query, tuple(exam_params))
    flat_records = cursor.fetchall()
    
    # Query overall institutional examination stats
    cursor.execute("SELECT AVG(`Total_Marks`) AS `avg_marks`, MAX(`Total_Marks`) AS `max_marks`, COUNT(DISTINCT `Subject`) AS `distinct_subj` FROM `examination`;")
    summary_db = cursor.fetchone()
    overall_avg_marks = round(float(summary_db["avg_marks"] or 0), 1) if summary_db and summary_db["avg_marks"] is not None else 0.0
    highest_marks = int(summary_db["max_marks"] or 0) if summary_db and summary_db["max_marks"] is not None else 0
    subjects_count = int(summary_db["distinct_subj"] or 0) if summary_db and summary_db["distinct_subj"] is not None else 0
    
    cursor.close()
    conn.close()
    
    # Map examination records by enrollment_no
    student_exam_map = {}
    for exam in flat_records:
        enr = exam["Enrollment_No"]
        if enr not in student_exam_map:
            student_exam_map[enr] = []
        student_exam_map[enr].append(exam)
        
    # The 3 canonical sections as strictly mapped:
    # Section A = CSE, Section B = ECE, Section C = EEE
    sections_config = [
        {
            "letter": "A",
            "dept_code": "CSE",
            "dept_name": "Computer Science and Engineering (CSE)"
        },
        {
            "letter": "B",
            "dept_code": "ECE",
            "dept_name": "Electronics and Communication Engineering (ECE)"
        },
        {
            "letter": "C",
            "dept_code": "EEE",
            "dept_name": "Electrical and Electronics Engineering (EEE)"
        }
    ]
    
    sections_data = []
    total_displayed_students = 0
    
    for sec in sections_config:
        # If user selected a specific section filter, filter accordingly
        if sec_filter and sec_filter not in [sec["letter"], sec["dept_code"]]:
            continue
            
        sec_students = [s for s in students_list if map_student_to_section(s) == sec["letter"]]
        student_items = []
        
        for s in sec_students:
            enr = s["Enrollment_No"]
            records = student_exam_map.get(enr, [])
            
            # If subject filter is active, only include if they have matching records
            if subj_filter and not records:
                continue
                
            avg_marks = round(sum(r["Total_Marks"] for r in records) / len(records), 1) if records else 0
            
            student_items.append({
                "student": s,
                "section_letter": sec["letter"],
                "semester": 6,
                "records": records,
                "average": avg_marks
            })
            total_displayed_students += 1
            
        # Add section if there are students
        if student_items or (not search_q and not subj_filter):
            sections_data.append({
                "letter": sec["letter"],
                "dept_code": sec["dept_code"],
                "dept_name": sec["dept_name"],
                "students": student_items,
                "student_count": len(student_items)
            })
            
    summary_stats = {
        "overall_avg": overall_avg_marks,
        "highest_marks": highest_marks,
        "subjects_count": subjects_count,
        "total_students": total_displayed_students
    }
    
    return render_template(
        "examination.html",
        sections_data=sections_data,
        summary_stats=summary_stats,
        records=flat_records,
        kpis=kpis,
        selected_sec=sec_filter,
        selected_subj=subj_filter,
        search_query=search_q,
        active_page="examination"
    )

@app.route("/fees")
@login_required
def fees_page():
    """
    Fees & Payments Module:
    Exact hierarchy:
      SECTION A — Computer Science and Engineering (CSE) -> 4 CSE Students -> Fee Details
      SECTION B — Electronics and Communication Engineering (ECE) -> 3 ECE Students -> Fee Details
      SECTION C — Electrical and Electronics Engineering (EEE) -> 3 EEE Students -> Fee Details
    Semester: Always Semester 6
    """
    kpis = get_kpis()
    sec_filter = request.args.get("section", "").strip().upper()
    status_filter = request.args.get("status", "").strip()
    search_q = request.args.get("q", "").strip()

    if DATA_MODE == "csv":
        students_list, flat_records, sections_data = _csv_module_data(
            "fees", section_filter=sec_filter, status_filter=status_filter, search_q=search_q
        )
        page = max(request.args.get("page", 1, type=int), 1)
        page_size = min(max(request.args.get("page_size", 10, type=int), 1), 100)
        sections_data, total_students = _paginate_sections(sections_data, page, page_size)
        return render_template(
            "fees.html",
            sections_data=sections_data,
            summary_stats={
                "total_fees": f"{int(flat_records['Total_Fees'].sum()):,}" if not flat_records.empty else "0",
                "total_collected": f"{int(flat_records['Paid_Amount'].sum()):,}" if not flat_records.empty else "0",
                "total_pending": f"{int(flat_records['Pending_Amount'].sum()):,}" if not flat_records.empty else "0",
                "pending_students": int((flat_records["Pending_Amount"] > 0).sum()) if not flat_records.empty else 0,
                "total_students": total_students,
            },
            records=flat_records.to_dict("records"),
            kpis=get_kpis(),
            selected_sec=sec_filter,
            selected_status=status_filter,
            search_query=search_q,
            page=page,
            page_size=page_size,
            total_students=total_students,
            active_page="fees",
        )
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all students (or filtered by search query)
    student_query = "SELECT * FROM `students` WHERE 1=1"
    student_params = []
    if search_q:
        student_query += " AND (`Name` LIKE %s OR `Enrollment_No` LIKE %s)"
        student_params.extend([f"%{search_q}%", f"%{search_q}%"])
    student_query += " ORDER BY `Enrollment_No`;"
    cursor.execute(student_query, tuple(student_params))
    students_list = cursor.fetchall()
    
    # Fetch fees records
    fee_query = """
        SELECT f.`Enrollment_No`, f.`Semester`, f.`Total_Fees`, f.`Paid_Amount`, 
               f.`Pending_Amount`, f.`Payment_Status`, f.`Fee_ID`, s.`Name`, s.`Department` 
        FROM `fees` f 
        LEFT JOIN `students` s ON f.`Enrollment_No` = s.`Enrollment_No` 
        WHERE 1=1
    """
    fee_params = []
    if status_filter:
        fee_query += " AND f.`Payment_Status` = %s"
        fee_params.append(status_filter)
    if search_q:
        fee_query += " AND (s.`Name` LIKE %s OR f.`Enrollment_No` LIKE %s)"
        fee_params.extend([f"%{search_q}%", f"%{search_q}%"])
    fee_query += " ORDER BY f.`Enrollment_No`;"
    cursor.execute(fee_query, tuple(fee_params))
    flat_records = cursor.fetchall()
    
    # Query overall institutional fee stats dynamically from MySQL fees table
    cursor.execute("""
        SELECT SUM(`Total_Fees`) AS `total`, 
               SUM(`Paid_Amount`) AS `paid`, 
               SUM(`Pending_Amount`) AS `pending`,
               COUNT(CASE WHEN `Pending_Amount` > 0 OR `Payment_Status` != 'Paid' THEN 1 END) AS `pending_count`
        FROM `fees`;
    """)
    summary_db = cursor.fetchone()
    total_fees = int(summary_db["total"] or 0) if summary_db and summary_db["total"] is not None else 0
    total_collected = int(summary_db["paid"] or 0) if summary_db and summary_db["paid"] is not None else 0
    total_pending = int(summary_db["pending"] or 0) if summary_db and summary_db["pending"] is not None else 0
    pending_students = int(summary_db["pending_count"] or 0) if summary_db and summary_db["pending_count"] is not None else 0
    
    cursor.close()
    conn.close()
    
    # Map fee records by enrollment_no
    student_fee_map = {r["Enrollment_No"]: r for r in flat_records}
    
    # The 3 canonical sections as strictly mapped:
    # Section A = CSE, Section B = ECE, Section C = EEE
    sections_config = [
        {
            "letter": "A",
            "dept_code": "CSE",
            "dept_name": "Computer Science and Engineering (CSE)"
        },
        {
            "letter": "B",
            "dept_code": "ECE",
            "dept_name": "Electronics and Communication Engineering (ECE)"
        },
        {
            "letter": "C",
            "dept_code": "EEE",
            "dept_name": "Electrical and Electronics Engineering (EEE)"
        }
    ]
    
    sections_data = []
    total_displayed_students = 0
    
    for sec in sections_config:
        # If user selected a specific section filter, filter accordingly
        if sec_filter and sec_filter not in [sec["letter"], sec["dept_code"]]:
            continue
            
        sec_students = [s for s in students_list if map_student_to_section(s) == sec["letter"]]
        student_items = []
        
        for s in sec_students:
            enr = s["Enrollment_No"]
            fee_rec = student_fee_map.get(enr)
            
            # If status filter is active and student didn't match, exclude
            if status_filter and not fee_rec:
                continue
                
            if not fee_rec:
                fee_rec = {
                    "Semester": 6,
                    "Total_Fees": 0,
                    "Paid_Amount": 0,
                    "Pending_Amount": 0,
                    "Payment_Status": "N/A"
                }
                
            student_items.append({
                "student": s,
                "section_letter": sec["letter"],
                "semester": 6,
                "fee": fee_rec
            })
            total_displayed_students += 1
            
        # Add section if there are students
        if student_items or (not search_q and not status_filter):
            sections_data.append({
                "letter": sec["letter"],
                "dept_code": sec["dept_code"],
                "dept_name": sec["dept_name"],
                "students": student_items,
                "student_count": len(student_items)
            })
            
    summary_stats = {
        "total_fees": f"{total_fees:,}",
        "total_collected": f"{total_collected:,}",
        "total_pending": f"{total_pending:,}",
        "pending_students": pending_students,
        "total_students": total_displayed_students
    }
    
    return render_template(
        "fees.html",
        sections_data=sections_data,
        summary_stats=summary_stats,
        records=flat_records,
        kpis=kpis,
        selected_sec=sec_filter,
        selected_status=status_filter,
        search_query=search_q,
        active_page="fees"
    )

@app.route("/reports")
@login_required
def reports_page():
    """Institutional Reports (Calculated via SQL aggregations from MySQL)."""
    kpis = get_kpis()
    if DATA_MODE == "csv":
        data = get_store()
        joined_att = data.attendance.merge(
            data.students[["Enrollment_No", "Department"]], on="Enrollment_No"
        )
        dept_stats = []
        for department, students in data.students.groupby("Department", sort=True):
            ids = set(students["Enrollment_No"])
            fees = data.fees[data.fees["Enrollment_No"].isin(ids)]
            exams = data.examination[data.examination["Enrollment_No"].isin(ids)]
            attendance = joined_att[joined_att["Enrollment_No"].isin(ids)]
            dept_stats.append({
                "department": department,
                "count": len(students),
                "avg_attendance": round(float(attendance["Attendance_Percentage"].mean()), 1),
                "avg_cgpa": round(float(students["CGPA"].mean()), 2),
                "total_fees": f"{int(fees['Total_Fees'].sum()):,}",
                "paid_fees": f"{int(fees['Paid_Amount'].sum()):,}",
                "pending_fees": f"{int(fees['Pending_Amount'].sum()):,}",
            })
        return render_template(
            "reports.html",
            kpis=kpis,
            dept_stats=dept_stats,
            exam_summary={
                "avg_marks": round(float(data.examination["Total_Marks"].mean()), 1),
                "highest_marks": int(data.examination["Total_Marks"].max()),
                "lowest_marks": int(data.examination["Total_Marks"].min()),
                "students_appeared": int(data.examination["Enrollment_No"].nunique()),
            },
            active_page="reports",
        )
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    dept_stats = []
    for dept in kpis["departments"]:
        cursor.execute("SELECT COUNT(*) as `count`, AVG(`CGPA`) as `avg_cgpa` FROM `students` WHERE `Department` = %s;", (dept,))
        stud_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT AVG(a.`Attendance_Percentage`) as `avg_att`
            FROM `attendance` a
            JOIN `students` s ON a.`Enrollment_No` = s.`Enrollment_No`
            WHERE s.`Department` = %s;
        """, (dept,))
        att_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT SUM(f.`Total_Fees`) as `total`, SUM(f.`Paid_Amount`) as `paid`, SUM(f.`Pending_Amount`) as `pending`
            FROM `fees` f
            JOIN `students` s ON f.`Enrollment_No` = s.`Enrollment_No`
            WHERE s.`Department` = %s;
        """, (dept,))
        fee_data = cursor.fetchone()
        
        dept_stats.append({
            "department": dept,
            "count": int(stud_data["count"] or 0),
            "avg_attendance": round(float(att_data["avg_att"] or 0), 1),
            "avg_cgpa": round(float(stud_data["avg_cgpa"] or 0), 2),
            "total_fees": f"{int(fee_data['total'] or 0):,}",
            "paid_fees": f"{int(fee_data['paid'] or 0):,}",
            "pending_fees": f"{int(fee_data['pending'] or 0):,}"
        })
        
    cursor.execute("""
        SELECT AVG(`Total_Marks`) AS `avg_marks`, 
               MAX(`Total_Marks`) AS `max_marks`, 
               MIN(`Total_Marks`) AS `min_marks`,
               COUNT(DISTINCT `Enrollment_No`) AS `students_appeared`
        FROM `examination`;
    """)
    exam_stats_row = cursor.fetchone()
    exam_summary = {
        "avg_marks": round(float(exam_stats_row["avg_marks"]), 1) if exam_stats_row and exam_stats_row["avg_marks"] is not None else 0.0,
        "highest_marks": int(exam_stats_row["max_marks"]) if exam_stats_row and exam_stats_row["max_marks"] is not None else 0,
        "lowest_marks": int(exam_stats_row["min_marks"]) if exam_stats_row and exam_stats_row["min_marks"] is not None else 0,
        "students_appeared": int(exam_stats_row["students_appeared"]) if exam_stats_row and exam_stats_row["students_appeared"] is not None else 0
    }

    cursor.close()
    conn.close()
    return render_template("reports.html", kpis=kpis, dept_stats=dept_stats, exam_summary=exam_summary, active_page="reports")


@app.route("/reports/export")
@login_required
def reports_export():
    """Download a real CSV report from the configured warehouse source."""
    report = request.args.get("report", "students").strip().lower()
    if DATA_MODE != "csv":
        return jsonify({"error": "Report export is currently implemented for CSV mode"}), 501

    data = get_store()
    if report in {"students", "attendance", "examination", "fees"}:
        frame = getattr(data, report).copy()
        filename = f"ifhe_{report}_semester5.csv"
    elif report == "departments":
        students = data.students
        attendance = data.attendance.merge(
            students[["Enrollment_No", "Department"]], on="Enrollment_No", how="inner"
        )
        rows = []
        for department, group in students.groupby("Department", sort=True):
            ids = set(group["Enrollment_No"])
            department_attendance = attendance[attendance["Enrollment_No"].isin(ids)]
            department_fees = data.fees[data.fees["Enrollment_No"].isin(ids)]
            rows.append({
                "Department": department,
                "Students": len(group),
                "Average_Attendance": round(float(department_attendance["Attendance_Percentage"].mean()), 1),
                "Average_CGPA": round(float(group["CGPA"].mean()), 2),
                "Total_Fees": int(department_fees["Total_Fees"].sum()),
                "Paid_Amount": int(department_fees["Paid_Amount"].sum()),
                "Pending_Amount": int(department_fees["Pending_Amount"].sum()),
            })
        frame = pd.DataFrame(rows)
        filename = "ifhe_department_summary_semester5.csv"
    else:
        return jsonify({
            "error": "Unsupported report",
            "available_reports": ["students", "attendance", "examination", "fees", "departments"],
        }), 400

    payload = frame.to_csv(index=False).encode("utf-8")
    return send_file(
        BytesIO(payload),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )

@app.route("/settings")
@login_required
def settings_page():
    """Settings Page showing Admin Profile and Institutional Scope."""
    return render_template("settings.html", user=session.get("user"), active_page="settings")

@app.route("/api/student/<enrollment_no>")
@login_required
def api_student(enrollment_no):
    """REST API endpoint returning integrated student profile from MySQL."""
    student_data = get_integrated_student(enrollment_no)
    if not student_data:
        return jsonify({"error": "Student not found", "enrollment_no": enrollment_no}), 404
    return jsonify(student_data)


@app.route("/api/kpis")
@login_required
def api_kpis():
    return jsonify(get_kpis())


@app.route("/api/students")
@login_required
def api_students():
    data = get_store() if DATA_MODE == "csv" else None
    if data is None:
        return jsonify({"error": "Student collection API is currently available in CSV mode only"}), 501
    query = request.args.get("q", "").strip().lower()
    department = request.args.get("department", "").strip()
    section = request.args.get("section", "").strip()
    semester = request.args.get("semester", type=int)
    page = max(request.args.get("page", 1, type=int), 1)
    page_size = min(max(request.args.get("page_size", 50, type=int), 1), 200)
    students = data.students
    if query:
        students = students[
            students["Enrollment_No"].str.lower().str.contains(query, na=False)
            | students["Name"].str.lower().str.contains(query, na=False)
        ]
    if department:
        students = students[students["Department"] == department]
    if section:
        students = students[students["Section"] == section]
    if semester is not None:
        students = students[students["Semester"] == semester]
    students = students.sort_values("Enrollment_No")
    total = len(students)
    rows = students.iloc[(page - 1) * page_size:page * page_size].to_dict("records")
    return jsonify({"items": rows, "page": page, "page_size": page_size, "total": total})


@app.route("/api/data-quality")
@login_required
def api_data_quality():
    return jsonify(get_store().quality.as_dict() if DATA_MODE == "csv" else {
        "mode": "mysql",
        "message": "Quality summary is supplied by the configured MySQL warehouse",
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
