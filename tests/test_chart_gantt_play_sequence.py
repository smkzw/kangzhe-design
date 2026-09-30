"""Charts/Gantt play() callback+RAF sequence in Node VM with labeled component stubs; no browser claim."""
from pathlib import Path
import subprocess, unittest

ROOT = Path(__file__).resolve().parents[1]

class ChartGanttPlaySequenceTest(unittest.TestCase):
    def test_play_renders_zero_first_and_grows_monotonically(self):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/chart_gantt_play_sequence.cjs'), str(ROOT)],
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
