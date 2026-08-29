import unittest

from canada_jobs.providers import _date, _date_from_millis, _deadline


class ProviderMetadataTests(unittest.TestCase):
    def test_iso_datetime_becomes_date(self):
        self.assertEqual(_date("2026-08-03T16:39:33-04:00"), "2026-08-03")

    def test_missing_date_is_explicit(self):
        self.assertEqual(_date(None), "Not specified")

    def test_labelled_deadline_is_extracted(self):
        self.assertEqual(_deadline("Application Deadline: September 12, 2026"),
                         "September 12, 2026")

    def test_unlabelled_date_is_not_treated_as_deadline(self):
        self.assertEqual(_deadline("The term begins September 12, 2026"), "Not specified")

    def test_lever_timestamp_is_converted(self):
        self.assertEqual(_date_from_millis(1787961600000), "2026-08-29")


if __name__ == "__main__":
    unittest.main()
