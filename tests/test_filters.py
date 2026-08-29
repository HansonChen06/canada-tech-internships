import unittest

from canada_jobs.filters import eligible


class EligibilityTests(unittest.TestCase):
    def test_canadian_software_intern_is_eligible(self):
        self.assertTrue(eligible("Software Engineering Intern", "Toronto, Ontario, Canada"))

    def test_coop_spelling_is_supported(self):
        self.assertTrue(eligible("Data Science Co-op", "Vancouver, BC, Canada"))

    def test_full_time_role_is_excluded(self):
        self.assertFalse(eligible("Senior Software Engineer", "Remote, Canada"))

    def test_non_canadian_role_is_excluded(self):
        self.assertFalse(eligible("Software Engineer Intern", "New York, United States"))

    def test_non_tech_intern_is_excluded(self):
        self.assertFalse(eligible("Legal Intern", "Toronto, Canada"))


if __name__ == "__main__":
    unittest.main()

