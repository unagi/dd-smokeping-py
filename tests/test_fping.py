import os
import unittest
from fping import Fping, FpingCheck


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
    def test_instance_tags(self):
        check = FpingCheck('dummy', {'tags': {'key1': 'global', 'key2': 'conflict_global'}}, {}, [])
        self.assertEquals(
                sorted(check._instance_tags({'addr': '127.0.0.1', 'tags': {'key2': 'conflict_instance', 'key3': 2}})),
                ['dst_addr:127.0.0.1', 'key1:global', 'key2:conflict_instance', 'key3:2']
        )

        with self.assertRaises(Exception) as err:
            check._instance_tags({})
        self.assertEquals(err.exception.args[0], 'All instances should have a \'tags\' parameter')

        with self.assertRaises(KeyError) as err:
            check._instance_tags({'tags': {}})
        self.assertEquals(err.exception.args[0], 'addr')

        self.assertEquals(
                sorted(check._instance_tags({'addr': '127.0.0.1', 'tags': {}})),
                ['dst_addr:127.0.0.1', 'key1:global', 'key2:conflict_global']
        )
