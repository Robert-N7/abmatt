import numpy as np

from abmatt.converters.convert_obj import ObjConverter, UVImporter, VertexColorExporter, VertexColorImporter
from abmatt.converters.obj import Obj
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
        VertexColorImporter(original, obj, [polygon]).convert()
        decoded = polygon.get_decoded().colors.rgba_colors
        expected = [173, 204, 163, 255]
        self.assertEqual(expected, list(decoded[0]))

    def test_create_obj_from_colors(self):
        original = self._get_brres('simple.brres')
        polygons = original.models[0].objects
        obj = Obj(self._get_tmp('.obj'), read_file=False)
        VertexColorExporter(original, obj, polygons).convert()
        colors = np.array([(*x.diffuse_color, x.dissolve) for x in obj.materials.values()]) * 255
        arr = [x.get_decoded().colors.rgba_colors
            for x in polygons if x.has_color0()]

        expected = np.unique(np.concatenate(arr), axis=0)
        self.assertTrue(np.array_equal(
            np.sort(expected, axis=0), np.sort(colors, axis=0)
        ))

    def test_obj_to_vert_color_eq(self):
        original = self._get_brres('beginner_course.brres')
        polygons = original.models[0].objects
        colors = [x.get_decoded().colors for x in polygons if x.has_color0()]
        for x in colors:
            x.consolidate()
        expected = [np.sort(np.unique(x.rgba_colors, axis=0))
                    for x in colors]
        obj = self._get_tmp('.obj')
        VertexColorExporter(original, obj, polygons).convert()
        default_amount = VertexColorImporter(original, obj, polygons, overwrite=True).convert()
        self.assertEqual(default_amount, 0)
        actual = [np.sort(np.unique(x.get_decoded().colors.rgba_colors, axis=0))
                    for x in polygons if x.has_color0()]
        for i in range(len(expected)):
            self.assertTrue(np.array_equal(
                expected[i],
                actual[i]
            ))

    def test_import_uvs(self):
        brres = self._get_brres('simple.brres')
        obj = self._get_test_fname('skp_simple_uv.obj')
        polygon = brres.models[0].objects[0]
        total = UVImporter(brres, obj, [polygon]).convert()
        self.assertEqual(total, 1)
        self.assertEqual(polygon.uv_count, 2)
        brres.save(self._get_tmp())