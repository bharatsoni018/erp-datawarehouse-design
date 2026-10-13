import sys
from app import app, get_db_connection

def test_reports():
    print("Testing Administration / Reports Page...")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "name": "System Administrator", "role": "admin"}
            
        res = client.get("/reports")
        assert res.status_code == 200, f"Expected status 200, got {res.status_code}"
        html = res.data.decode("utf-8")
        
        # 1. Check Header
        assert "Administration / Reports" in html
        assert "Institutional Reports" in html
        assert "High-level academic and operational summary statistics across departments" in html
        
        # 2. Check Department Summary Table
        assert "Department Summary" in html
        assert "Department" in html
        assert "Enrolled Students" in html
        assert "Avg. Attendance" in html
        assert "Avg. CGPA" in html
        assert "Total Fees" in html
        assert "Collected" in html
        assert "Pending Dues" in html
        
        # Check departments
        assert "Computer Science &amp; Engineering" in html
        assert "Electronics &amp; Communication Engineering" in html
        assert "Electrical &amp; Electronics Engineering" in html
        
        # 3. Check Institution-wide Highlights
        assert "Institution-wide Highlights" in html
        assert "Overall Students:" in html
        assert "Batch Avg Attendance:" in html
        assert "Overall Avg CGPA:" in html
        assert "Total Outstanding Dues:" in html
        
        # 4. Check Examination Summary
        assert "Examination Summary" in html
        assert "Average Marks:" in html
        assert "Highest Marks:" in html
        assert "Lowest Marks:" in html
        assert "Students Appeared:" in html
        
        # Fetch expected values from database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT AVG(`Total_Marks`) AS avg_m, MAX(`Total_Marks`) AS max_m, MIN(`Total_Marks`) AS min_m, COUNT(DISTINCT `Enrollment_No`) AS stud_count FROM `examination`;")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        avg_m = f"{round(float(row['avg_m']), 1)}"
        max_m = f"{int(row['max_m'])}"
        min_m = f"{int(row['min_m'])}"
        stud_count = f"{int(row['stud_count'])} Students"
        
        print(f"Verified Examination values in DB: avg={avg_m}, max={max_m}, min={min_m}, appeared={stud_count}")
        assert avg_m in html, f"Expected avg_marks {avg_m} in HTML"
        assert max_m in html, f"Expected highest_marks {max_m} in HTML"
        assert min_m in html, f"Expected lowest_marks {min_m} in HTML"
        assert stud_count in html, f"Expected students_appeared {stud_count} in HTML"
        
        print("All Reports page tests passed successfully!")

if __name__ == "__main__":
    test_reports()
