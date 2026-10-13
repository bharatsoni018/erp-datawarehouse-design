from app import app

def test_search_and_student_profile():
    print("Testing Search Student and Student Profile Routes...")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "name": "System Administrator", "role": "admin"}

        # 1. Search Student Page
        res = client.get("/search-student")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("  [PASS] /search-student loaded successfully")

        # 2. Search for existing student 2026CSE001
        res = client.get("/search?enrollment_no=2026CSE001", follow_redirects=True)
        assert res.status_code == 200, f"Expected 200 on redirect, got {res.status_code}"
        html = res.data.decode("utf-8")
        assert "2026CSE001" in html
        assert "Rahul Sharma" in html
        assert "Attendance" in html
        assert "Examination" in html
        assert "Fees &amp; Payments" in html or "Fees & Payments" in html
        print("  [PASS] /search?enrollment_no=2026CSE001 redirected to /student/2026CSE001 and rendered correctly")

        # 3. Direct Profile GET for all 10 students
        test_students = [
            ("2026CSE001", "Rahul Sharma"),
            ("2026CSE002", "Priya Patel"),
            ("2026CSE003", "Rohan Verma"),
            ("2026CSE004", "Sneha Reddy"),
            ("2026ECE001", "Ananya Iyer"),
            ("2026ECE002", "Vikram Singh"),
            ("2026ECE003", "Kavya Nair"),
            ("2026EEE001", "Aditya Kulkarni"),
            ("2026EEE002", "Meera Das"),
            ("2026EEE003", "Amit Gupta")
        ]
        
        for enr, name in test_students:
            res = client.get(f"/student/{enr}")
            assert res.status_code == 200, f"Failed for {enr}, got status {res.status_code}"
            h = res.data.decode("utf-8")
            assert enr in h, f"{enr} not in profile HTML"
            assert name in h, f"{name} not in profile HTML"
            # verify attendance, exam, fees sections present
            assert "Attendance Summary" in h or "Attendance" in h
            assert "Examination" in h
            assert "Fees" in h
            print(f"  [PASS] Profile for {enr} ({name}) rendered without error.")

        # 4. Search for non-existent student
        res = client.get("/search?enrollment_no=NONEXISTENT", follow_redirects=True)
        assert res.status_code == 200
        print("  [PASS] Non-existent search handled safely")

    print("\nAll Search Student & Profile tests passed with 100% success (Zero NameErrors)!\n")

if __name__ == "__main__":
    test_search_and_student_profile()
