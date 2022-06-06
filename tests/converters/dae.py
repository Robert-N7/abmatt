from converters.dae import Dae
from tests.lib import AbmattTest


class DaeConverterTest(AbmattTest):
    def test_blender_unused_mat_loads_correct_material(self):
        dae = Dae(self._get_test_fname('blender-unused-mat.dae'))
        for node in dae.get_scene():
            if node.geometries:
                for geometry in node.geometries:
                    self.assertEqual('Material__454-material', geometry.material_name)