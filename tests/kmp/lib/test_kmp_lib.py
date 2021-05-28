import os

from abmatt.kmp.kmp import Kmp
from tests.lib import AbmattTest


class KmpTest(AbmattTest):
    kmp_file_path = AbmattTest._get_test_fname('kmp_files')

    def _get_test_fname(self, filename):
        path = super()._get_test_fname(filename)
        if not os.path.exists(path):
            return os.path.join(KmpTest.kmp_file_path, filename)
        return path

    def _get_kmp(self, filename):
        return Kmp(os.path.join(self.kmp_file_path, filename))