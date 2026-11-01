import unittest

from app import app, get_integrated_student
from data_store import DataStore


class CsvModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = DataStore.from_csv()

    def test_authoritative_dataset_counts_and_quality(self):
        self.assertEqual(self.store.quality.row_counts, {
            "students": 1000,
            "attendance": 5000,
            "examination": 5000,
            "fees": 1000,
        })
        self.assertEqual(self.store.quality.duplicate_student_ids, 0)
        self.assertEqual(set(self.store.kpis()["departments"]), {"CSE", "ECE", "EEE", "IT", "AIDS", "AIML"})
        self.assertEqual(self.store.kpis()["semesters"], [5])

    def test_student_360_join(self):
        profile = self.store.student("stu0001")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["personal"]["Enrollment_No"], "STU0001")
        self.assertEqual(profile["attendance"]["count"], 5)
        self.assertEqual(profile["examination"]["count"], 5)
        self.assertIsNotNone(profile["fees"])

    def test_csv_routes_and_pagination(self):
        client = app.test_client()
        with client:
            login = client.post(
                "/login",
                data={"username": "admin", "password": "admin123"},
                follow_redirects=True,
            )
            self.assertEqual(login.status_code, 200)
            for path in ("/dashboard", "/students", "/attendance", "/examination", "/fees", "/reports"):
                self.assertEqual(client.get(path).status_code, 200)
            students = client.get("/api/students?page=2&page_size=25").get_json()
            self.assertEqual(students["page"], 2)
            self.assertEqual(len(students["items"]), 25)
            self.assertEqual(students["total"], 1000)
            quality = client.get("/api/data-quality").get_json()
            self.assertEqual(quality["row_counts"]["students"], 1000)

    def test_report_exports(self):
        client = app.test_client()
        with client:
            client.post("/login", data={"username": "admin", "password": "admin123"})
            for report, expected in (("students", 1000), ("attendance", 5000), ("examination", 5000), ("fees", 1000), ("departments", 6)):
                response = client.get(f"/reports/export?report={report}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/csv")
                self.assertEqual(len(response.data.decode("utf-8").splitlines()) - 1, expected)
            self.assertEqual(client.get("/reports/export?report=unknown").status_code, 400)

    def test_fee_profile_links_keep_students_isolated(self):
        client = app.test_client()
        with client:
            client.post("/login", data={"username": "admin", "password": "admin123"})
            fee_page = client.get("/fees")
            self.assertEqual(fee_page.status_code, 200)
            self.assertIn(b'href="/student/STU0001"', fee_page.data)
            for enrollment_no in ("STU0001", "STU0002"):
                profile = client.get(f"/student/{enrollment_no}")
                self.assertEqual(profile.status_code, 200)
                self.assertIn(enrollment_no.encode(), profile.data)
                other = "STU0002" if enrollment_no == "STU0001" else "STU0001"
                profile_data = get_integrated_student(enrollment_no)
                other_data = get_integrated_student(other)
                self.assertNotEqual(
                    profile_data["fees"]["Total_Fees"],
                    other_data["fees"]["Total_Fees"],
                )
                self.assertIn(
                    str(profile_data["fees"]["Pending_Amount"]).encode(),
                    profile.data,
                )
                self.assertNotIn(
                    other_data["personal"]["Name"].encode(),
                    profile.data,
                )

    def test_invalid_student_profile_urls_are_explicit(self):
        client = app.test_client()
        with client:
            client.post("/login", data={"username": "admin", "password": "admin123"})
            self.assertEqual(client.get("/student/").status_code, 400)
            self.assertEqual(client.get("/student/NOT-A-STUDENT").status_code, 404)
            self.assertIn(b"Student not found", client.get("/student/NOT-A-STUDENT").data)


if __name__ == "__main__":
    unittest.main()
