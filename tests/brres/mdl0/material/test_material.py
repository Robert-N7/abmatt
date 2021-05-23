import unittest
from copy import deepcopy
from abmatt.brres.mdl0.material.material import Material
from tests import lib
from tests.lib import node_eq


class TestMaterial(lib.TestBeginner):
    def test_deepcopy(self):
        original_mats = self.brres.models[0].materials
        new_mats = deepcopy(original_mats)
        self.assertTrue(node_eq(original_mats, new_mats))


if __name__ == '__main__':
    unittest.main()