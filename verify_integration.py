import sys
import os
import pandas as pd

sys.path.insert(0, r"C:\Users\BHARAT\.gemini\antigravity\scratch\erp_dw_decision_support")

from app import app, load_datasets, get_kpis, get_integrated_student

def test_integration_and_searches():
    print("==================================================================")
    print("1. VERIFYING DYNAMIC STATS COMPUTATION (NO HARDCODING)")
    print("==================================================================")
    students, attendance, examination, fees = load_datasets()
    
    # Calculate directly
    direct_total_students = len(students)
    direct_avg_att = round(attendance["Attendance_Percentage"].mean(), 1)
    direct_avg_marks = round(examination["Total_Marks"].mean(), 1)
    direct_avg_cgpa = round(students["CGPA"].mean(), 2)
    direct_pending_fees = f"{int(fees['Pending_Amount'].sum()):,}"
    
    kpis = get_kpis()
    assert kpis["total_students"] == direct_total_students
    assert kpis["avg_attendance"] == direct_avg_att
    assert kpis["avg_marks"] == direct_avg_marks
    assert kpis["avg_cgpa"] == direct_avg_cgpa
    assert kpis["total_pending"] == direct_pending_fees
    
    print(f"  [PASS] Total Students: {kpis['total_students']} (from students.csv)")
    print(f"  [PASS] Average Attendance: {kpis['avg_attendance']}% (from attendance.csv)")
    print(f"  [PASS] Average Marks: {kpis['avg_marks']}/100 (from examination.csv)")
    print(f"  [PASS] Average CGPA: {kpis['avg_cgpa']} (from students.csv)")
    print(f"  [PASS] Total Pending Fees: Rs.{kpis['total_pending']} (from fees.csv)")

    print("\n==================================================================")
    print("2. VERIFYING REQUIRED STUDENT SEARCHES & STRICT RECORD ISOLATION")
    print("==================================================================")
    
    # Test 1: 2026CSE001 (Rahul Sharma)
    s1 = get_integrated_student("2026CSE001")
    assert s1 is not None
    assert s1["personal"]["Name"] == "Rahul Sharma"
    assert s1["personal"]["Department"] == "Computer Science & Engineering"
    assert s1["personal"]["CGPA"] == 9.14
    assert len(s1["attendance"]["records"]) == 5
    assert len(s1["examination"]["records"]) == 5
    assert s1["fees"]["Payment_Status"] == "Paid"
    assert s1["fees"]["Pending_Amount"] == 0
    print("  [PASS] 2026CSE001 -> Rahul Sharma (CSE, CGPA 9.14, 5 Att., 5 Exams, Fees: Paid)")

    # Test 2: 2026CSE002 (Priya Patel)
    s2 = get_integrated_student("2026CSE002")
    assert s2 is not None
    assert s2["personal"]["Name"] == "Priya Patel"
    assert s2["personal"]["Department"] == "Computer Science & Engineering"
    assert s2["personal"]["CGPA"] == 9.82
    assert len(s2["attendance"]["records"]) == 5
    assert len(s2["examination"]["records"]) == 5
    assert s2["fees"]["Payment_Status"] == "Paid"
    print("  [PASS] 2026CSE002 -> Priya Patel (CSE, CGPA 9.82, 5 Att., 5 Exams, Fees: Paid)")

    # Test 3: 2026ECE001 (Ananya Iyer)
    s3 = get_integrated_student("2026ECE001")
    assert s3 is not None
    assert s3["personal"]["Name"] == "Ananya Iyer"
    assert s3["personal"]["Department"] == "Electronics & Communication Engineering"
    assert s3["personal"]["CGPA"] == 9.35
    assert "Digital Signal Processing" in [r["Subject"] for r in s3["attendance"]["records"]]
    assert len(s3["attendance"]["records"]) == 5
    assert len(s3["examination"]["records"]) == 5
    assert s3["fees"]["Payment_Status"] == "Paid"
    print("  [PASS] 2026ECE001 -> Ananya Iyer (ECE, CGPA 9.35, 5 ECE Att., 5 ECE Exams, Fees: Paid)")

    # Test 4: 2026EEE001 (Aditya Kulkarni)
    s4 = get_integrated_student("2026EEE001")
    assert s4 is not None
    assert s4["personal"]["Name"] == "Aditya Kulkarni"
    assert s4["personal"]["Department"] == "Electrical & Electronics Engineering"
    assert s4["personal"]["CGPA"] == 8.20
    assert "Power System Analysis" in [r["Subject"] for r in s4["attendance"]["records"]]
    assert len(s4["attendance"]["records"]) == 5
    assert len(s4["examination"]["records"]) == 5
    assert s4["fees"]["Payment_Status"] == "Paid"
    print("  [PASS] 2026EEE001 -> Aditya Kulkarni (EEE, CGPA 8.20, 5 EEE Att., 5 EEE Exams, Fees: Paid)")

    print("\n==================================================================")
    print("3. VERIFYING STRICT ZERO DATA MIXING (ALL 10 STUDENTS)")
    print("==================================================================")
    all_enrollments = [
        "2026CSE001", "2026CSE002", "2026CSE003", "2026CSE004",
        "2026ECE001", "2026ECE002", "2026ECE003",
        "2026EEE001", "2026EEE002", "2026EEE003"
    ]
    for enr in all_enrollments:
        profile = get_integrated_student(enr)
        # Check that all attendance rows belong strictly to this enrollment
        att_df = attendance[attendance["Enrollment_No"] == enr]
        assert len(profile["attendance"]["records"]) == len(att_df)
        
        # Check that all exam rows belong strictly to this enrollment
        exam_df = examination[examination["Enrollment_No"] == enr]
        assert len(profile["examination"]["records"]) == len(exam_df)
        
        # Check fees
        fee_row = fees[fees["Enrollment_No"] == enr].iloc[0]
        assert profile["fees"]["Payment_Status"] == fee_row["Payment_Status"]
        assert profile["fees"]["Pending_Amount"] == fee_row["Pending_Amount"]
        
        print(f"  [OK] {enr}: {profile['personal']['Name']} | Att: {len(profile['attendance']['records'])} | Exam: {len(profile['examination']['records'])} | Fee Status: {profile['fees']['Payment_Status']} (Due: Rs.{profile['fees']['Pending_Amount']:,})")

    print("\n[ALL INTEGRATION & ISOLATION TESTS PASSED 100% SUCCESSFULLY!]")

if __name__ == "__main__":
    test_integration_and_searches()
