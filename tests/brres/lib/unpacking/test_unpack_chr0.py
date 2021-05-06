from tests.lib import AbmattTest


class TestUnpackChr0(AbmattTest):
    def test_unpack_kuribo_walk(self):
        b = self._get_brres('kuribo.brres')
        self.assertTrue(b.chr0)
        # todo check chr0
