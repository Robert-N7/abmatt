from abmatt.converters.convert_dae import DaeConverter
from tests.lib import AbmattTest, CheckPositions


class TestConvertMapModel(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.MAP = cls._get_brres('map_model.brres')

    def test_map_model_converts_bones_correctly(self):
        # Export the map model
        dae = self._get_tmp('.dae')
        DaeConverter(self.MAP, dae, encode=False).convert()
        converter = DaeConverter(self._get_tmp('.brres'), dae)
        converter.load_model()
        self.assertTrue(CheckPositions.model_equal(self.MAP.models[0], converter.mdl0))