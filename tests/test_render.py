import tempfile
import unittest
from pathlib import Path

from canada_jobs.model import Job
from canada_jobs.render import markdown, write_outputs


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.job = Job("abc", "Example", "Software Intern", "Toronto, Canada",
                       "https://example.com/job", "greenhouse", "2026-08-29", "2026-08-29")

    def test_markdown_has_role_and_link(self):
        output = markdown([self.job], "2026-08-29 12:00")
        self.assertIn("Software Intern", output)
        self.assertIn("[Apply](https://example.com/job)", output)

    def test_writes_all_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_outputs(root, [self.job], "2026-08-29 12:00")
            self.assertTrue((root / "README.md").exists())
            self.assertTrue((root / "data/jobs.json").exists())
            self.assertTrue((root / "data/jobs.csv").exists())


if __name__ == "__main__":
    unittest.main()

