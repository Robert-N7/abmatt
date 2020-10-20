import unittest

from autofix import AutoFix
from brres import Brres


class ChangePolyMatTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.brres = Brres('../brres_files/beginner_course.brres')
        self.poly = self.brres.models[0].objects[0]
        self.mat = self.poly.get_material()
        self.simple = Brres('../brres_files/simple.brres')
        self.output = '../brres_files/test.brres'
        super().__init__(*args, **kwargs)

    def test_from_same_brres(self):
        mat = self.brres.models[0].materials[0]
        self.poly.set_material(mat)
        # Test the material is correct
        self.assertTrue(self.poly.get_material().name == mat.name)
        # Test that the previous material is gone
        self.assertIsNone(self.poly.parent.get_material_by_name(self.mat.name))
        self.brres.save(self.output, True)

    def test_from_diff_brres(self):
        mat = self.simple.models[0].materials[0]
        self.poly.set_material(mat)
        # Test the material
        self.assertTrue(self.poly.get_material().name == mat.name)
        self.brres.save(self.output, True)

    def test_no_mat_removal(self):
        # in this test change a poly that has a shared material
        # and make sure the material still exists
        # First set up a shared material
        mat = self.brres.models[0].materials[0]
        self.poly.set_material(mat)  # now mat should have 2 polys
        self.assertTrue(len(mat.polygons) == 2)
        self.poly.set_material(self.brres.models[0].materials[2])
        self.assertIsNotNone(self.brres.models[0].get_material_by_name(mat.name))
        self.brres.save(self.output, True)


if __name__ == '__main__':
    unittest.main()
    AutoFix.quit()
