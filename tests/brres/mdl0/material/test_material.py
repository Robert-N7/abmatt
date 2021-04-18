import unittest
from copy import deepcopy
from abmatt.brres.mdl0.material.material import Material
from tests import lib


class TestMaterial(lib.TestBeginner):
    def test_deepcopy(self):
        original_mats = self.brres.models[0].materials
        new_mats = deepcopy(original_mats)
        self.assertEqual(original_mats, new_mats)


if __name__ == '__main__':
    unittest.main()