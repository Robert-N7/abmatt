from abmatt.converters.convert_obj import ObjConverter, obj_mats_to_vertex_colors
from tests.lib import AbmattTest, CheckPositions


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

    def test_load_patch(self):
        original = self._get_brres('simple.brres')
        replace = original.models[0].objects[0]
        converter = ObjConverter(original,
                                 self._get_test_fname('3ds_simple.obj'),
                                 flags=ObjConverter.PATCH,
                                 include=[replace.name],
                                 ).convert()
        item = [x for x in converter.mdl0.objects if x.name == replace.name][0]
        self.assertIsNot(replace, item)

    def test_save_load_eq(self):
        original = self._get_brres('beginner_course.brres')
        converter = ObjConverter(original, self._get_tmp('.obj'),
                                 encode=False).convert()
        encoder = ObjConverter(self._get_tmp('.brres'), converter.mdl_file).convert()
        self.assertTrue(CheckPositions.positions_equal(original.models[0].vertices, encoder.mdl0.vertices))

    def test_load_mats_to_colors(self):
        original = self._get_brres('simple.brres')
        obj = self._get_test_fname('skp_simple.obj')
        polygon = original.models[0].objects[0]
        obj_mats_to_vertex_colors([polygon], obj)
        decoded = original.models[0].objects[-1].get_decoded().colors.rgba_colors
        expected = [149, 166, 91, 255]
        self.assertEqual(expected, list(decoded[0]))
