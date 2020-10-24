import unittest

from brres import Brres


class TestSimple(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.brres = Brres('../brres_files/simple.brres')


class TestWater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brres = Brres('../brres_files/water_course.brres')
