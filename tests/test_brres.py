import os
import sys
import unittest

from abmatt.brres import Brres
from tests.lib import AbmattTest


class MyTestCase(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.brres = cls._get_brres('beginner_course.brres')
        cls.original_model = cls.brres.models[0]
        cls.test_file = cls._get_brres_fname('test.brres')
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)
        cls.brres.save(cls.test_file, True)
        if not os.path.exists(cls.test_file):
            raise Exception('Failed to save test file')
        cls.test = Brres(cls.test_file)
        cls.test_model = cls.test.models[0]

    def test_correct_amount_of_objects(self):
        self.assertEqual(len(self.brres.models), 1)
        self.assertEqual(len(self.brres.textures), 29)
        self.assertEqual(len(self.brres.pat0), 1)
        self.assertEqual(len(self.brres.srt0), 1)

    def test_materials_equal(self):
        self.assertTrue(len(self.original_model.materials) > 0)
        for mat in self.original_model.materials:
            self.assertEqual(mat, self.test_model.get_material_by_name(mat.name))

    def test_polygons_equal(self):
        original_len = len(self.original_model.objects)
        self.assertTrue(original_len > 0)
        self.assertTrue(original_len == len(self.test_model.objects))

if __name__ == '__main__':
    unittest.main()
