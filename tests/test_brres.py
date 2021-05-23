import os
import sys
import unittest

from abmatt.brres import Brres
from tests.lib import AbmattTest, node_eq


class TestBrresLoadsCorrectly(AbmattTest):
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

    def test_materials_equal(self):
        self.assertTrue(len(self.original_model.materials) > 0)
        for mat in self.original_model.materials:
            self.assertEqual(mat, self.test_model.get_material_by_name(mat.name))

    def test_polygons_equal(self):
        original_len = len(self.original_model.objects)
        self.assertTrue(original_len > 0)
        self.assertTrue(original_len == len(self.test_model.objects))

    # Currently unsupported
    # def test_load_and_save_brres_with_text_file(self):
    #     brres = self._get_brres('kuribo_with_txt.brres')
    #     brres.save(self._get_tmp('.brres'), overwrite=True)


class TestBrresSaveEqual(AbmattTest):
    def _test_save_eq(self, brres):
        tmp = self._get_tmp('.brres')
        brres.save(tmp, overwrite=True)
        return node_eq(Brres(tmp), brres)

    def test_save_beginner(self):  # has pat0 and srt0
        self.assertTrue(self._test_save_eq(self._get_brres('beginner_course.brres')))

    def test_save_farm(self):  # has scn0
        self.assertTrue(self._test_save_eq(self._get_brres('farm_course.brres')))

    def test_save_pocha(self):  # has clr0 and chr0
        self.assertTrue(self._test_save_eq(self._get_brres('pocha.brres')))

    def test_save_flagb2(self):  # has shp0
        self.assertTrue(self._test_save_eq(self._get_brres('FlagB2.brres')))

    def test_save_with_unknown_files(self):  # various txt files
        self.assertTrue(self._test_save_eq(self._get_brres('kuribo_with_txt.brres')))


if __name__ == '__main__':
    unittest.main()
