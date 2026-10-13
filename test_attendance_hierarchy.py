import mysql.connector
from db_config import get_db_config

def test_mapping():
    conn = mysql.connector.connect(**get_db_config(include_db=True))
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM students ORDER BY Enrollment_No;')
    students = cursor.fetchall()

    cursor.execute('SELECT * FROM attendance ORDER BY Enrollment_No, Attendance_ID;')
    attendance_records = cursor.fetchall()
    cursor.close()
    conn.close()

    sections_def = [
        {
            'section_letter': 'A',
            'dept_code': 'CSE',
            'dept_title': 'Computer Science and Engineering (CSE)',
            'dept_match': 'Computer Science'
        },
        {
            'section_letter': 'B',
            'dept_code': 'ECE',
            'dept_title': 'Electronics and Communication Engineering (ECE)',
            'dept_match': 'Electronics & Communication'
        },
        {
            'section_letter': 'C',
            'dept_code': 'EEE',
            'dept_title': 'Electrical and Electronics Engineering (EEE)',
            'dept_match': 'Electrical & Electronics'
        }
    ]

    att_map = {}
    for r in attendance_records:
        enr = r['Enrollment_No']
        if enr not in att_map:
            att_map[enr] = []
        att_map[enr].append(r)

    total_records = 0
    total_pcts = []
    low_att_count = 0

    for sec in sections_def:
        sec_students = [s for s in students if sec['dept_match'] in s['Department']]
        print(f"\n=======================================================")
        print(f"  SECTION {sec['section_letter']} — {sec['dept_title']} ({len(sec_students)} Students)")
        print(f"=======================================================")
        for s in sec_students:
            s_att = att_map.get(s['Enrollment_No'], [])
            total_records += len(s_att)
            total_pcts.extend([a['Attendance_Percentage'] for a in s_att])
            avg = round(sum(a['Attendance_Percentage'] for a in s_att) / len(s_att), 1) if s_att else 0
            if avg < 75:
                low_att_count += 1
            print(f"  * {s['Name']} [{s['Enrollment_No']}] - Section {sec['section_letter']} • Semester 6 (Avg: {avg}%)")
            for a in s_att:
                status = 'Good' if a['Attendance_Percentage'] >= 85 else ('Average' if a['Attendance_Percentage'] >= 75 else 'Low')
                print(f"      - {a['Subject']}: {a['Attendance_Percentage']}% [{status}]")

    overall_avg = round(sum(total_pcts) / len(total_pcts), 1) if total_pcts else 0
    print("\nSummary Cards Data:")
    print(f"  Overall Attendance: {overall_avg}%")
    print(f"  Total Students: {len(students)}")
    print(f"  Low Attendance: {low_att_count} Students")

if __name__ == "__main__":
    test_mapping()
