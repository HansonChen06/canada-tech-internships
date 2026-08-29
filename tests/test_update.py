import unittest

from canada_jobs.model import Job
from canada_jobs.update import merge


class MergeTests(unittest.TestCase):
    def test_first_seen_survives_refresh(self):
        old = Job("1", "Acme", "Software Intern", "Toronto, Canada", "u", "lever", "2026-01-01", "2026-01-01")
        new = Job("1", "Acme", "Software Intern", "Toronto, Canada", "u", "lever", "2026-08-29", "2026-08-29")
        result = merge([new], {"1": old}, "2026-08-29")
        self.assertEqual(result[0].first_seen, "2026-01-01")
        self.assertEqual(result[0].last_seen, "2026-08-29")

    def test_closed_role_disappears(self):
        old = Job("1", "Acme", "Software Intern", "Toronto, Canada", "u", "lever", "2026-01-01", "2026-01-01")
        self.assertEqual(merge([], {"1": old}, "2026-08-29"), [])

    def test_source_failure_keeps_last_known_role(self):
        old = Job("1", "Acme", "Software Intern", "Toronto, Canada", "u", "lever", "2026-01-01", "2026-08-28")
        self.assertEqual(merge([], {"1": old}, "2026-08-29", ["Acme"]), [old])


if __name__ == "__main__":
    unittest.main()
