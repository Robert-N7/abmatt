from abmatt.brres import Brres
from abmatt.converters.convert_dae import DaeConverter2
from tests.lib import AbmattTest


class DaeConverterTest(AbmattTest):
    def test_convert_with_json(self):
        brres = self._get_brres('beginner_course.brres')
        dae_file = self._get_test_fname('beginner.dae')
        converter = DaeConverter2(Brres('tmp.brres', readFile=False), dae_file)
        converter.load_model()
        self._test_mats_equal(converter.brres.models[0].materials, brres.models[0].materials)
