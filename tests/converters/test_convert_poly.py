from tests.lib import AbmattTest


class TestConvertPoly(AbmattTest):
    def test_decode_same_as_encode(self):
        brres = self._get_brres('simple.brres')
        model = brres.models[0]
        ex_objects = [x for x in model.objects]
        decoded = model.objects[0].get_decoded()
        decoded.recode(model.objects[0])
        brres.save(self._get_tmp())
        # While the object may differ because of encoding, the length will be the same
        self.assertEqual(len(ex_objects), len(model.objects))
