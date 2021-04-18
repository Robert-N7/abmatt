import unittest
from copy import deepcopy

from abmatt.brres.mdl0.material.material import Material
from abmatt.converters.convert_mats_to_json import MatsToJsonConverter
from tests.lib import TestBeginner


class TestConvertMatToJson(TestBeginner):
    def test_export_and_load_are_equal(self):
        temp = self._get_test_fname('tmp.json')
        materials = self.brres.models[0].materials
        exporter = MatsToJsonConverter(temp)
        exporter.export(materials)
        updated = [Material(x.name) for x in materials]
        importer = MatsToJsonConverter(temp)
        mats = importer.load()
        importer.load_into(updated)
        self.assertTrue(self._test_mats_equal(materials, updated))
        self.assertTrue(self._test_mats_equal(materials, mats))


if __name__ == '__main__':
    unittest.main()