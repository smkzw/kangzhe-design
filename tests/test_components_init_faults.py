"""Component init fault injection in Node VM with labeled stubs; no model or browser acceptance."""
from pathlib import Path
import subprocess, unittest

ROOT = Path(__file__).resolve().parents[1]

class ComponentInitFaultsTest(unittest.TestCase):
    def test_components_roll_back_partial_mounts(self):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/components_init_faults.cjs'), str(ROOT)],
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
