from abmatt.brres import Brres
from tests.lib import AbmattTest


class TestUnpackBrres(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.BB_SIMPLE = cls._get_brres('bb_simple.brres')
        cls.BB_MODEL = cls.BB_SIMPLE.models[0]

    def test_linked_bones(self):
        for poly in self.BB_MODEL.objects:
            self.assertEqual(poly.linked_bone.name, 'TransN_' + poly.name)