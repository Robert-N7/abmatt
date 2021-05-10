import sys
import unittest

from tests.integration.lib import IntegTest


class TestTex0(IntegTest):
    def test_add_tex0(self):
        self.assertTrue(self._abmatt_simple('add tex0:test_files/simple/Wax_02.jpg format:ia8'))

    def test_remove_tex0(self):
        self.assertTrue(self._abmatt_simple('-c remove -t tex0:Wax_02'))

    def test_resize_dimension_tex0(self):
        self.assertTrue(self._abmatt_simple('-c set -t tex0:Wax_02 -k dimensions -v 300,300'))

    def test_format_tex0(self):
        self.assertTrue(self._abmatt_simple('-c set -t tex0:Wax_02 -k format -v rgb5a3'))


if __name__ == '__main__':
    unittest.main()
