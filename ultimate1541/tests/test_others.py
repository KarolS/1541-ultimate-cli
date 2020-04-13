import unittest

import ultimate1541

class TestSplitPath(unittest.TestCase):

    def test_split_path(self):
        self.assertEqual(ultimate1541.split_path('/Usb0/A/B'), ['Usb0', 'A', 'B'])