from abmatt.brres import Brres
from tests.integration.lib import IntegTest
from tests.lib import AbmattTest


class TestSaveBrres(IntegTest, AbmattTest):
    def test_save_moonview(self):
        self.assertTrue(self._abmatt('-b brres_files/crazy_cannon.brres -d test_files/tmp.brres -o --moonview'))
        b = Brres(self._get_tmp('.brres', False))
        self.assertFalse(b.check_moonview())
        self.assertFalse(b.MOONVIEW)