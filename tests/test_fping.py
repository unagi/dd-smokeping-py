import os, unittest
from fping import Fping


class TestFping(unittest.TestCase):
    def test_run(self):
        fping = Fping(['127.0.0.1', '127.0.0.2', '169.254.254.254'], 2)
        result = fping.run()
        self.assertLess(result['127.0.0.1'], 10)
        self.assertLess(result['127.0.0.2'], 10)
        self.assertIsNone(result['169.254.254.254'])

    def test_run_command_not_found(self):
        env = os.environ.copy()
        os.environ["PATH"] = ""
        fping = Fping(['8.8.8.8'], 2)
        with self.assertRaises(StandardError) as err:
            result = fping.run()
        self.assertEquals(err.exception.message, 'Command not found: fping')
        os.environ["PATH"] = env["PATH"]

    def test_run_invalid_address(self):
        fping = Fping(['invalid_address_format.0'], 2)
        with self.assertRaises(StandardError) as err:
            result = fping.run()
        self.assertEquals(err.exception.message, 'Invalid addresses : invalid_address_format.0')
