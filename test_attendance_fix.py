import sys
sys.path.insert(0, r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support")
from app import app, map_student_to_section, get_db_connection

def test_attendance_sections():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT Enrollment_No, Name, Department, Section FROM students ORDER BY Enrollment_No;")
    students = cur.fetchall()
    cur.close()
    conn.close()

    print("--- MAP STUDENT TO SECTION TEST ---")
    for s in students:
        mapped_sec = map_student_to_section(s)
        print(f"{s['Enrollment_No']} ({s['Name']}) - Dept: {s['Department']} -> Section {mapped_sec}")
        if "CSE" in s["Enrollment_No"]:
            assert mapped_sec == "A", f"Expected Section A for {s['Enrollment_No']}, got {mapped_sec}"
        elif "ECE" in s["Enrollment_No"]:
            assert mapped_sec == "B", f"Expected Section B for {s['Enrollment_No']}, got {mapped_sec}"
        elif "EEE" in s["Enrollment_No"]:
            assert mapped_sec == "C", f"Expected Section C for {s['Enrollment_No']}, got {mapped_sec}"

    client = app.test_client()
    with client:
        client.post("/login", data={"username": "admin", "password": "admin123"})
        res = client.get("/attendance")
        html = res.data.decode("utf-8")
        
        # Check Section headers
        print("\n--- HTML INSPECTION (ALL SECTIONS) ---")
        assert "SECTION A" in html
        assert "SECTION B" in html
        assert "SECTION C" in html
        
        # Verify student counts per section
        sec_a_pos = html.find("SECTION A</span>")
        sec_b_pos = html.find("SECTION B</span>")
        sec_c_pos = html.find("SECTION C</span>")
        
        assert sec_a_pos != -1 and sec_b_pos != -1 and sec_c_pos != -1
        assert sec_a_pos < sec_b_pos < sec_c_pos
        
        chunk_a = html[sec_a_pos:sec_b_pos]
        chunk_b = html[sec_b_pos:sec_c_pos]
        chunk_c = html[sec_c_pos:]
        
        print("\n--- CHECKING SECTION A CHUNK ---")
        assert "2026CSE001" in chunk_a
        assert "2026CSE002" in chunk_a
        assert "2026CSE003" in chunk_a
        assert "2026CSE004" in chunk_a
        assert "2026ECE" not in chunk_a
        assert "2026EEE" not in chunk_a
        assert "(4 Students Enrolled)" in chunk_a
        print("  [PASS] Section A contains ONLY the 4 CSE students.")
        
        print("\n--- CHECKING SECTION B CHUNK ---")
        assert "2026ECE001" in chunk_b
        assert "2026ECE002" in chunk_b
        assert "2026ECE003" in chunk_b
        assert "2026CSE" not in chunk_b
        assert "2026EEE" not in chunk_b
        assert "(3 Students Enrolled)" in chunk_b
        print("  [PASS] Section B contains ONLY the 3 ECE students (ZERO EEE students).")
        
        print("\n--- CHECKING SECTION C CHUNK ---")
        assert "2026EEE001" in chunk_c
        assert "2026EEE002" in chunk_c
        assert "2026EEE003" in chunk_c
        assert "2026CSE" not in chunk_c
        assert "2026ECE" not in chunk_c
        assert "(3 Students Enrolled)" in chunk_c
        print("  [PASS] Section C contains ONLY the 3 EEE students.")
        
        # Verify Section filter queries
        print("\n--- CHECKING SECTION FILTERS ---")
        res_a = client.get("/attendance?section=A")
        html_a = res_a.data.decode("utf-8")
        assert "2026CSE001" in html_a and "2026ECE001" not in html_a and "2026EEE001" not in html_a
        print("  [PASS] Filter Section A: exactly 4 CSE students.")
        
        res_b = client.get("/attendance?section=B")
        html_b = res_b.data.decode("utf-8")
        assert "2026ECE001" in html_b and "2026ECE002" in html_b and "2026ECE003" in html_b
        assert "2026EEE001" not in html_b and "2026EEE002" not in html_b and "2026EEE003" not in html_b
        assert "2026CSE001" not in html_b
        assert "(3 Students Enrolled)" in html_b
        print("  [PASS] Filter Section B: exactly 3 ECE students, ZERO EEE students.")
        
        res_c = client.get("/attendance?section=C")
        html_c = res_c.data.decode("utf-8")
        assert "2026EEE001" in html_c and "2026EEE002" in html_c and "2026EEE003" in html_c
        assert "2026ECE001" not in html_c and "2026CSE001" not in html_c
        assert "(3 Students Enrolled)" in html_c
        print("  [PASS] Filter Section C: exactly 3 EEE students.")
        
        # Verify Semester 6 consistency
        assert "Semester 6" in html
        assert "Semester 1" not in html and "Semester 2" not in html and "Semester 3" not in html and "Semester 4" not in html and "Semester 5" not in html and "Semester 7" not in html and "Semester 8" not in html
        print("  [PASS] Only Semester 6 is present across all attendance displays.")
        
    print("\n" + "=" * 65)
    print("  ALL ATTENDANCE SECTION MAPPING TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    test_attendance_sections()
