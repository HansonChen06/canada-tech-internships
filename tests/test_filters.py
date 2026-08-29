import unittest
from datetime import date

from canada_jobs.filters import currently_recruiting, eligible
from canada_jobs.model import Job


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

    def _job(self, posted="2026-08-01", deadline="Not specified"):
        return Job("1", "Acme", "Software Intern", "Toronto, Canada", "u",
                   "ashby", "2026-08-01", "2026-08-01", posted, deadline)

    def test_old_posting_is_excluded_even_if_ats_returns_it(self):
        self.assertFalse(currently_recruiting(self._job(posted="2024-09-10"),
                                              date(2026, 8, 29)))

    def test_expired_deadline_is_excluded(self):
        self.assertFalse(currently_recruiting(self._job(deadline="May 17th, 2026"),
                                              date(2026, 8, 29)))

    def test_future_deadline_is_kept(self):
        self.assertTrue(currently_recruiting(self._job(deadline="25 October 2026"),
                                             date(2026, 8, 29)))


if __name__ == "__main__":
    unittest.main()
