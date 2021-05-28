import os

from abmatt.kmp.kmp import Kmp
from debug.file_compare import file_compare
from tests.kmp.lib.test_kmp_lib import KmpTest


class TestPack(KmpTest):
    def _test_pack_eq(self, fname):
        original = Kmp(self._get_test_fname(fname))
        name = original.name
        original.save(self._get_tmp('kmp'))
        if not file_compare(name, original.name):
            new = Kmp(original.name)
            self.assertTrue(original == new)
            raise ValueError(f'{name} packed not equal!')

    def test_beginner_pack_eq(self):
        self._test_pack_eq('beginner.kmp')

    def test_casino_pack_eq(self):
        self._test_pack_eq('casino.kmp')