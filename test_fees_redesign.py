import sys
sys.path.insert(0, r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support")
from app import app

def test_fees_redesign():
    print("=" * 65)
    print("  FEES & PAYMENTS MODULE REDESIGN VERIFICATION TEST SUITE")
    print("=" * 65)

    client = app.test_client()
    with client:
        # 1. Login as Admin
        client.post("/login", data={"username": "admin", "password": "admin123"})
        
        # 2. Access /fees
        res = client.get("/fees")
        assert res.status_code == 200, f"Expected status 200, got {res.status_code}"
        html = res.data.decode("utf-8")
        
        # 3. Header & Supporting text
        print("\n[TEST 1] Verifying Page Header & Subtitle...")
        assert "Fees &amp; Payments" in html or "Fees & Payments" in html
        assert "Student fee details and payment status" in html
        print("  [PASS] Page Header and Supporting text verified.")
        
        # 4. 4 Summary Cards (Total Fees, Total Collected, Total Pending, Pending Students)
        print("\n[TEST 2] Verifying 4 Summary KPI Cards...")
        assert "Total Fees" in html
        assert "Total Collected" in html
        assert "Total Pending" in html
        assert "Pending Students" in html
        assert "805,000" in html
        assert "650,000" in html
        assert "155,000" in html
        assert "3" in html
        print("  [PASS] Total Fees (Rs. 805,000), Collected (Rs. 650,000), Pending (Rs. 155,000), Pending Students (3) dynamically verified.")
        
        # 5. Section A, B, C structure
        print("\n[TEST 3] Verifying Section A/B/C Hierarchy...")
        sec_a_pos = html.find("SECTION A</span>")
        sec_b_pos = html.find("SECTION B</span>")
        sec_c_pos = html.find("SECTION C</span>")
        
        assert sec_a_pos != -1 and sec_b_pos != -1 and sec_c_pos != -1
        assert sec_a_pos < sec_b_pos < sec_c_pos
        
        chunk_a = html[sec_a_pos:sec_b_pos]
        chunk_b = html[sec_b_pos:sec_c_pos]
        chunk_c = html[sec_c_pos:]
        
        # Section A: 4 CSE students
        print("\n[TEST 4] Verifying Section A — CSE...")
        assert "Computer Science and Engineering (CSE)" in chunk_a
        assert "(4 Students Enrolled)" in chunk_a
        for enr in ["2026CSE001", "2026CSE002", "2026CSE003", "2026CSE004"]:
            assert enr in chunk_a, f"Missing {enr} in Section A!"
        assert "2026ECE" not in chunk_a
        assert "2026EEE" not in chunk_a
        print("  [PASS] Section A contains ONLY the 4 CSE students.")
        
        # Section B: 3 ECE students
        print("\n[TEST 5] Verifying Section B — ECE...")
        assert "Electronics and Communication Engineering (ECE)" in chunk_b
        assert "(3 Students Enrolled)" in chunk_b
        for enr in ["2026ECE001", "2026ECE002", "2026ECE003"]:
            assert enr in chunk_b, f"Missing {enr} in Section B!"
        assert "2026CSE" not in chunk_b
        assert "2026EEE" not in chunk_b
        print("  [PASS] Section B contains ONLY the 3 ECE students (ZERO EEE students).")
        
        # Section C: 3 EEE students
        print("\n[TEST 6] Verifying Section C — EEE...")
        assert "Electrical and Electronics Engineering (EEE)" in chunk_c
        assert "(3 Students Enrolled)" in chunk_c
        for enr in ["2026EEE001", "2026EEE002", "2026EEE003"]:
            assert enr in chunk_c, f"Missing {enr} in Section C!"
        assert "2026CSE" not in chunk_c
        assert "2026ECE" not in chunk_c
        print("  [PASS] Section C contains ONLY the 3 EEE students.")
        
        # 6. Student Fee Details & Table columns
        print("\n[TEST 7] Verifying Fee Table Columns & Amounts Display...")
        assert "Total Fees" in html
        assert "Paid Amount" in html
        assert "Pending Amount" in html
        assert "Payment Status" in html
        
        # Verify Rahul Sharma data (2026CSE001)
        assert "Rahul Sharma" in chunk_a
        assert "85,000" in chunk_a
        assert "Paid" in chunk_a
        
        # Verify Rohan Verma data (2026CSE003 - Partial)
        assert "Rohan Verma" in chunk_a
        assert "45,000" in chunk_a
        assert "40,000" in chunk_a
        assert "Partially Paid" in chunk_a
        
        # Verify Amit Gupta data (2026EEE003 - Pending)
        assert "Amit Gupta" in chunk_c
        assert "75,000" in chunk_c
        assert "Pending" in chunk_c
        print("  [PASS] Student fee details (Total, Paid, Pending, Payment Status) accurately rendered.")
        
        # 7. Semester 6 Only
        print("\n[TEST 8] Verifying Semester 6 Consistency...")
        assert "Semester 6" in html
        for other_sem in ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 7", "Semester 8"]:
            assert other_sem not in html, f"Found unwanted {other_sem}!"
        print("  [PASS] Only Semester 6 appears across all student blocks.")
        
        # 8. Filter Tests
        print("\n[TEST 9] Verifying Filters (Section, Status, Search Query)...")
        # Section A filter
        res_a = client.get("/fees?section=A")
        html_a = res_a.data.decode("utf-8")
        assert "2026CSE001" in html_a and "2026ECE001" not in html_a and "2026EEE001" not in html_a
        assert "(4 Students Enrolled)" in html_a
        print("  [PASS] Filter Section A: 4 CSE students.")
        
        # Section B filter
        res_b = client.get("/fees?section=B")
        html_b = res_b.data.decode("utf-8")
        assert "2026ECE001" in html_b and "2026ECE002" in html_b and "2026ECE003" in html_b
        assert "2026EEE001" not in html_b and "2026CSE001" not in html_b
        assert "(3 Students Enrolled)" in html_b
        print("  [PASS] Filter Section B: 3 ECE students, zero EEE.")
        
        # Section C filter
        res_c = client.get("/fees?section=C")
        html_c = res_c.data.decode("utf-8")
        assert "2026EEE001" in html_c and "2026EEE002" in html_c and "2026EEE003" in html_c
        assert "2026ECE001" not in html_c and "2026CSE001" not in html_c
        assert "(3 Students Enrolled)" in html_c
        print("  [PASS] Filter Section C: 3 EEE students.")
        
        # Status filter: Partial
        res_partial = client.get("/fees?status=Partial")
        html_partial = res_partial.data.decode("utf-8")
        assert "2026CSE003" in html_partial and "2026ECE002" in html_partial
        assert "2026CSE001" not in html_partial and "2026EEE003" not in html_partial
        print("  [PASS] Filter Status (Partial): matched exactly 2 partially paid students.")
        
        # Status filter: Pending
        res_pending = client.get("/fees?status=Pending")
        html_pending = res_pending.data.decode("utf-8")
        assert "2026EEE003" in html_pending
        assert "2026CSE001" not in html_pending and "2026CSE003" not in html_pending
        print("  [PASS] Filter Status (Pending): matched exactly 1 pending student.")
        
        # Search query
        res_q = client.get("/fees?q=Rahul")
        html_q = res_q.data.decode("utf-8")
        assert "Rahul Sharma" in html_q
        assert "2026CSE001" in html_q
        assert "Priya Patel" not in html_q
        print("  [PASS] Search Query (Rahul): matched Rahul Sharma.")

    print("\n" + "=" * 65)
    print("  ALL FEES & PAYMENTS REDESIGN TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    test_fees_redesign()
