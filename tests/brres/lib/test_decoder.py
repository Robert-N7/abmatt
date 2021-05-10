from abmatt.brres.lib.decoder import ColorDecoder
from tests.lib import AbmattTest


class TestDecoder(AbmattTest):
    def test_decoding_rgb565_colors(self):
        brres = self._get_brres('puchi_pakkun.brres')
        colors = brres.models[1].colors[0]
        decoded = ColorDecoder.decode_data(colors)
        first_three = [(255, 255, 255, 255), (191, 191, 191, 255), (167, 167, 167, 255)]
        for i in range(3):
            self.assertTrue((first_three[i] == decoded[i]).all())
