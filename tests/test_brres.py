import os
import sys
import unittest

from abmatt.brres import Brres


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.brres = Brres('../brres_files/beginner_course.brres')
        self.original_model = self.brres.models[0]
        self.test_file = '../brres_files/test.brres'
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.brres.save(self.test_file, True)
        if not os.path.exists(self.test_file):
            raise Exception('Failed to save test file')
        self.test = Brres(self.test_file)
        self.test_model = self.test.models[0]

    def test_correct_amount_of_objects(self):
        self.assertEqual(len(self.brres.models), 1)
        self.assertEqual(len(self.brres.textures), 29)
        self.assertEqual(len(self.brres.pat0), 1)
        self.assertEqual(len(self.brres.srt0), 1)

    def test_materials_equal(self):
        for mat in self.original_model.materials:
            self.assertEqual(mat, self.test_model.get_material_by_name(mat.name))

    def test_polygons_equal(self):
        for x in self.original_model.polygons:
            self.assertEqual(x, )

if __name__ == '__main__':
    unittest.main()
    sys.exit(0)
