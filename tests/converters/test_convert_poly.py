from copy import deepcopy

from brres.mdl0.polygon import Polygon
from tests.lib import AbmattTest


class TestConvertPoly(AbmattTest):
    def test_decode_same_as_encode(self):
        brres = self._get_brres('simple.brres')
        model = brres.models[0]
        polygon = model.objects[0]
        original = deepcopy(polygon)
        decoded = polygon.get_decoded()
        decoded.recode(polygon)
        self.assertEqual([
            polygon.name,
            polygon.vertices,
            polygon.face_count
        ], [
            original.name,
            original.vertices,
            original.face_count
        ])
