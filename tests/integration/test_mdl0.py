import sys
import unittest

from tests.integration.lib import IntegTest


class TestMdl0(IntegTest):
    def test_add_mdl0(self):
        self.assertTrue(self._abmatt_simple('-c add -t mdl0:test_files/water_course.dae'))

    def test_remove_mdl0(self):
        self.assertTrue(self._abmatt_simple('-c remove -t mdl0:course'))


if __name__ == '__main__':
    unittest.main()
