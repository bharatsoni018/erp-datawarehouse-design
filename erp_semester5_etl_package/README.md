# ERP Data Warehouse — Semester 5 Demo ETL Dataset

## Files
- `students.csv` — 1,000 student dimension rows, matching the existing `students` table columns (12 columns).
- `attendance.csv` — 5,000 subject-level attendance rows.
- `examination.csv` — 5,000 subject-level examination rows.
- `fees.csv` — 1,000 semester fee rows.
- `source_cleaned.csv` — cleaned/normalized copy of the original input for traceability.
- `etl_quality_report.json` — counts, validation results and methodology notes.
- `schema.sql` — non-destructive schema creation script matching the current project tables.

## ETL performed
1. Trimmed/normalized identifiers and categorical values.
2. Parsed date columns and standardized them to ISO date/time formats in the cleaned source.
3. Imputed missing Attendance and Study_Hours with medians and missing Scholarship with `No`.
4. Reassigned department values to six requested demo branches: CSE, ECE, EEE, IT, AIDS, AIML. This is an explicit synthetic demo transformation, not a claim about original source records.
5. Assigned all target records to Semester 5 and Academic Year 2025-2026.
6. Replaced placeholder `Student_#` labels with generated fictional names and added synthetic phone, email, section and address fields.
7. Generated five subject records per student for attendance and examinations, because the source has only one marks/attendance record per student.
8. Derived Internal_Marks (0–40) from Assignment_Marks and Midterm_Marks; derived External_Marks (0–60) from Final_Marks; recalculated totals and grades.
9. Generated synthetic fee amounts, paid/pending balances and payment status for demonstration only.
10. Validated unique student IDs, foreign-key references, mark/attendance ranges and fee arithmetic.

## Important integrity note
This is a **synthetic demonstration dataset based on the uploaded source**, not verified real student records. Names/contact details, branch reassignment, subject-level expansion, semester, CGPA mapping, and fees are generated or transformed for the demo. Clearly disclose this in your project report. Do not present synthetic fee records as real payments.

## Import safety
`schema.sql` creates tables if absent but does not delete data. Your existing `database_setup.py` uses `TRUNCATE`; do not run it against a database containing records you want to preserve. Before importing these CSVs into an existing database, check for `Enrollment_No` collisions and back up your data.
