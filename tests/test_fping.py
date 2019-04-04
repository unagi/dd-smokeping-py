import os
import unittest
from fping import merged_tag_list, Fping, FpingCheck


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
        with self.assertRaises(Exception) as err:
            fping.run()
        self.assertEquals(err.exception.args[0], 'Command not found: fping')
        os.environ["PATH"] = env["PATH"]

    def test_run_invalid_address(self):
        fping = Fping(['invalid_address_format.0'], 2)
        with self.assertRaises(Exception) as err:
            fping.run()
        self.assertEquals(err.exception.args[0], 'Invalid addresses : invalid_address_format.0')


class TestFpingCheck(unittest.TestCase):
    def test_run(self):
        check = FpingCheck('dummy', {'tags': ['key1:global', 'key2:conflict_global']}, {},
                           [{'addr': '127.0.0.1', 'tags': []}])
        check.run()

    def test_run_with_duplicate_data(self):
        with self.assertRaises(Exception) as err:
            FpingCheck('dummy', {'tags': ['key1:global', 'key2:conflict_global']}, {},
                       [{'addr': '127.0.0.1', 'tags': {}}, {'addr': '127.0.0.1', 'tags': []}])
            self.assertEquals(err.exception.args[0], 'Duplicate address found: 127.0.0.1')


class TestFunction(unittest.TestCase):
    def test_instance_tags(self):
        self.assertEquals(
                merged_tag_list(['key1:global', 'key2:conflict_global'], []),
                ['key1:global', 'key2:conflict_global']
        )

    def test_instance_tags_with_override(self):
        self.assertEquals(
                merged_tag_list(['key1:global', 'key2:conflict_global'], ['key2:override', 'key3:2']),
                ['key1:global', 'key2:override', 'key3:2']
        )
