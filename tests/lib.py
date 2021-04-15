import os
import unittest

from abmatt.autofix import AutoFix
from abmatt.brres import Brres


def get_base_path():
    path = new_path = os.path.abspath(__file__)
    fname = None
    while fname != 'abmatt':
        path = new_path
        new_path, fname = os.path.split(path)
    return path


class AbmattTest(unittest.TestCase):
    @classmethod
    def tearDown(cls):
        AutoFix.quit()

    @staticmethod
    def _get_brres_fname(filename):
        return os.path.join(AbmattTest.base_path, 'brres_files', filename)

    @staticmethod
    def _get_test_fname(filename):
        return os.path.join(AbmattTest.base_path, 'test_files', filename)

    @staticmethod
    def _get_brres(filename):
        return Brres(AbmattTest._get_brres_fname(filename))


AbmattTest.base_path = get_base_path()
AbmattTest.main_path = os.path.join(AbmattTest.base_path, 'abmatt', '__main__.py')


class TestSimple(AbmattTest):
    @classmethod
    def setUpClass(self):
        self.brres = Brres(self._get_brres_fname('simple.brres'))


class TestWater(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.brres = Brres(cls._get_brres('water_course.brres'))
