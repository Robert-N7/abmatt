from abmatt.converters.convert_obj import ObjConverter
from tests.lib import AbmattTest


class TestConvertObj(AbmattTest):
    def test_load_map_model(self):
        mdl_file = self._get_test_fname('map_model.obj')
        converter = ObjConverter(self._get_tmp('.brres'), mdl_file)
        converter.load_model()
        map_bone = converter.mdl0.bones[0]
        self.assertEqual('map', map_bone.name)
        pos_ld = map_bone.child
        self.assertEqual('posLD', pos_ld.name)
        pos_ru = pos_ld.next
        self.assertEqual('posRU', pos_ru.name)
        for poly in converter.mdl0.objects:
            self.assertEqual(map_bone, poly.linked_bone)
            self.assertEqual(map_bone, poly.visible_bone)
