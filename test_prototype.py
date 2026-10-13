import sys
import os
import mysql.connector

sys.path.insert(0, r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support")

from db_config import get_db_config, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER
from app import app, get_db_connection, get_kpis, get_integrated_student

def test_mysql_and_application():
    print("=" * 65)
    print("  COMPREHENSIVE MYSQL 8.0 & FLASK INTEGRATION TEST SUITE")
    print("=" * 65)

    # TEST 1: MySQL 8.0 Reachability
    print("\n[TEST 1] Checking MySQL 8.0 Community Server reachability...")
    conn = get_db_connection()
    assert conn.is_connected(), "MySQL connection failed!"
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT VERSION() AS ver;")
    ver = cursor.fetchone()["ver"]
    print(f"  [PASS] Connected to MySQL Server at {MYSQL_HOST}:{MYSQL_PORT} (Version: {ver})")

    # TEST 2: Database Existence
    print("\n[TEST 2] Checking database 'erp_academic_db'...")
    cursor.execute("SELECT DATABASE() AS db;")
    db_name = cursor.fetchone()["db"]
    assert db_name == "erp_academic_db", f"Expected db 'erp_academic_db', got '{db_name}'"
    print(f"  [PASS] Active database is '{db_name}'")

    # TEST 3: Tables Existence
    print("\n[TEST 3] Checking required tables existence...")
    cursor.execute("SHOW TABLES;")
    tables = [list(r.values())[0] for r in cursor.fetchall()]
    for tbl in ["students", "attendance", "examination", "fees"]:
        assert tbl in tables, f"Missing table '{tbl}' in MySQL!"
    print(f"  [PASS] All 4 tables found: {', '.join(tables)}")

    # TEST 4-7: Row Counts and Data in Tables
    print("\n[TEST 4-7] Verifying table records...")
    counts = {}
    for tbl in ["students", "attendance", "examination", "fees"]:
        cursor.execute(f"SELECT COUNT(*) AS c FROM `{tbl}`;")
        counts[tbl] = cursor.fetchone()["c"]
    assert counts["students"] == 10, f"Expected 10 students, got {counts['students']}"
    assert counts["attendance"] == 50, f"Expected 50 attendance records, got {counts['attendance']}"
    assert counts["examination"] == 50, f"Expected 50 examination records, got {counts['examination']}"
    assert counts["fees"] == 10, f"Expected 10 fees records, got {counts['fees']}"
    print(f"  [PASS] students: {counts['students']} rows")
    print(f"  [PASS] attendance: {counts['attendance']} rows")
    print(f"  [PASS] examination: {counts['examination']} rows")
    print(f"  [PASS] fees: {counts['fees']} rows")

    # TEST 8: Enrollment_No Relationships & Foreign Keys
    print("\n[TEST 8] Verifying Enrollment_No relationships across all 10 students...")
    enrollments = [
        "2026CSE001", "2026CSE002", "2026CSE003", "2026CSE004",
        "2026ECE001", "2026ECE002", "2026ECE003",
        "2026EEE001", "2026EEE002", "2026EEE003"
    ]
    for enr in enrollments:
        profile = get_integrated_student(enr)
        assert profile is not None, f"Profile for {enr} returned None!"
        assert profile["personal"]["Enrollment_No"] == enr
        assert len(profile["attendance"]["records"]) == 5
        assert len(profile["examination"]["records"]) == 5
        assert profile["fees"]["Semester"] == 6
        print(f"  [OK] {enr} -> {profile['personal']['Name']} (CGPA: {profile['personal']['CGPA']}, Att: 5 recs, Exam: 5 recs, Fee: {profile['fees']['Payment_Status']})")
    print("  [PASS] Multi-table relational queries confirmed for all 10 students.")

    cursor.close()
    conn.close()

    # TEST 9-18: Flask Client Authentication & Routing Flow
    print("\n[TEST 9-18] Verifying Flask Routes & Authentication Flow...")
    client = app.test_client()

    # Test 11: Fresh start opens Login FIRST
    res = client.get("/")
    assert res.status_code == 200
    assert b"Admin Login" in res.data
    assert b"ICFAI Foundation for Higher Education (IFHE), Hyderabad" in res.data
    assert b"Unified Academic Data Management System" not in res.data
    assert b"Welcome, Admin" not in res.data
    print("  [PASS] Fresh start: http://127.0.0.1:5000 opens LOGIN PAGE FIRST.")

    # Test 12: Dashboard is protected
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    print("  [PASS] /dashboard is protected and redirects unauthenticated users to login.")

    # Test 10: Admin Login
    with client:
        res = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Dashboard" in res.data
        assert b"Student Summary" in res.data
        assert b"Attendance Summary" in res.data
        assert b"Examination Summary" in res.data
        assert b"Fees &amp; Payments Summary" in res.data or b"Fees & Payments Summary" in res.data
        assert b"Department Overview" in res.data
        assert b"Recent Students" not in res.data
        print("  [PASS] Admin login succeeded and loaded Consolidated Summary Dashboard from MySQL.")

        # Test 13 & 14: Search 2026CSE001 (Unified Profile from 4 MySQL tables)
        res_search = client.get("/search?enrollment_no=2026CSE001", follow_redirects=True)
        assert res_search.status_code == 200
        assert b"Rahul Sharma" in res_search.data
        assert b"2026CSE001" in res_search.data
        assert b"Personal Information" in res_search.data
        assert b"Attendance" in res_search.data
        assert b"Examination" in res_search.data
        assert b"Fees &amp; Payments" in res_search.data or b"Fees & Payments" in res_search.data
        assert b"9.14" in res_search.data
        print("  [PASS] Search 2026CSE001 returned complete Unified Profile from all 4 MySQL tables.")

        # Test 15: Consolidated Dashboard summary consistency
        res_dash = client.get("/dashboard")
        content = res_dash.data.decode("utf-8")
        assert "Recent Students" not in content
        assert "Total Students" in content
        assert "Overall Attendance" in content
        print("  [PASS] Consolidated Dashboard summary confirmed active without detailed tables or search history.")

        # Test 16: Logout
        res_logout = client.get("/logout", follow_redirects=True)
        assert res_logout.status_code == 200
        assert b"Admin Login" in res_logout.data
        print("  [PASS] Logout successfully destroys session.")

    # Test 17: After logout, accessing /dashboard redirects to Login
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    print("  [PASS] After logout, accessing /dashboard redirects to Login.")

    # Test 18: Restart simulation
    app.secret_key = os.urandom(24).hex()
    client_new = app.test_client()
    res = client_new.get("/")
    assert res.status_code == 200
    assert b"Admin Login" in res.data
    print("  [PASS] Restarted app successfully presents Login page.")

    print("\n" + "=" * 65)
    print("  ALL 18 MYSQL & APPLICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    test_mysql_and_application()
