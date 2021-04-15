import sys
import unittest

from tests.integration.lib import IntegTest


class TestConvert(IntegTest):
    def test_to_dae(self):
        self.assertTrue(self._abmatt_simple('convert to test_files/test.dae'))

    def test_to_obj(self):
        self.assertTrue(self._abmatt_simple('convert to test_files/test.obj'))

    def test_from_3ds_dae(self):
        self.assertTrue(self._abmatt('convert test_files/3ds_simple.DAE to brres_files/test.brres -o'))

    def test_from_3ds_obj(self):
        self.assertTrue(self._abmatt('convert test_files/3ds_simple.obj to brres_files/test.brres -o'))

    def test_from_skp_obj(self):
        self.assertTrue(self._abmatt('convert test_files/skp_simple.obj to brres_files/test.brres -o'))

    def test_from_skp_dae(self):
        self.assertTrue(self._abmatt('convert test_files/skp_simple.dae to brres_files/test.brres -o'))


if __name__ == '__main__':
    unittest.main()