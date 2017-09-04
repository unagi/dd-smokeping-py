import unittest
from fping import Fping


class TestFping(unittest.TestCase):
    def test_run(self):
        fping = Fping(['127.0.0.1', '127.0.0.2', '169.254.254.254'], 2)
        result = fping.run()
        self.assertLess(result['127.0.0.1'], 10)
        self.assertLess(result['127.0.0.2'], 10)
        self.assertIsNone(result['169.254.254.254'])
