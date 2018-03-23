from unittest import TestCase

import chff

class Testchff(TestCase):
    def test_is_string(self):
        s = chff.hello()
        self.assertTrue(isinstance(s, str))
