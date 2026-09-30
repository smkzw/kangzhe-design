"""Host fault injection; no simulated model or browser acceptance."""
from pathlib import Path
import subprocess, unittest

ROOT = Path(__file__).resolve().parents[1]

class ExampleCleanupTest(unittest.TestCase):
    def test_example_rolls_back_and_releases_all_handles(self):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/a03_cleanup.cjs'),
             str(ROOT / 'examples/validation/KZ6-0929-A03/html-ppt/a03.js')],
            text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
