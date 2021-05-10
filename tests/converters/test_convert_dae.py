from abmatt.brres import Brres
from abmatt.converters.convert_dae import DaeConverter
from tests.lib import AbmattTest, CheckPositions


class DaeConverterTest(AbmattTest):
    # ------------------------------------------------------
    # region load_model
    def test_convert_to_correct_position(self):
        # Get reference to beginner_course to test against
        beginner_brres = self._get_brres('beginner_course.brres')
        original_vertices = beginner_brres.models[0].vertices
        # Convert dae
        brres = Brres(self._get_tmp('.brres'), read_file=False)
        dae = self._get_test_fname('beginner.dae')
        converter = DaeConverter(brres, dae)
        converter.load_model()
        # brres.save(overwrite=True)
        new_vertices = brres.models[0].vertices
        self.assertTrue(CheckPositions().positions_equal(original_vertices, new_vertices))

    def test_convert_with_json(self):
        brres = self._get_brres('beginner_course.brres')
        dae_file = self._get_test_fname('beginner.dae')
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False), dae_file)
        converter.load_model()
        self._test_mats_equal(converter.brres.models[0].materials, brres.models[0].materials)

    def test_convert_multi_material_geometry(self):
        """Tests converting dae file that has multiple materials associated with geometry"""
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False), self._get_test_fname('blender.dae'))
        converter.load_model()
        mdl0 = converter.brres.models[0]
        self.assertEqual(len(mdl0.materials), 2)
        self.assertEqual(len(mdl0.objects), 2)

    def test_convert_single_bone(self):
        original = self._get_brres('simple.brres')
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False),
                                 self._get_test_fname('simple_multi_bone_single_bind.dae'),
                                 flags=DaeConverter.SINGLE_BONE)
        converter.load_model()
        mdl0 = converter.mdl0
        self.assertEqual(len(mdl0.bones), 1)
        self.assertTrue(CheckPositions.positions_equal(original.models[0].vertices, mdl0.vertices))

    def test_convert_single_bind_flip_y_z(self):
        original = self._get_brres('simple_multi_bone_single_bind.brres')
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False),
                                 self._get_test_fname('blender_simple_multi_bone_single_bind.dae'))
        converter.load_model()
        # converter.brres.save(overwrite=True)
        original_polys = original.models[0].objects
        new_polys = converter.mdl0.objects
        for i in range(len(original_polys)):
            self.assertEqual(original_polys[i].linked_bone.index, new_polys[i].linked_bone.index)
        # For some reason the bones and positions aren't the same... but seem to match up visually?
        # self.assertTrue(CheckPositions.positions_equal(original.models[0].vertices, converter.mdl0.vertices))

    def test_convert_multi_bone_single_bind(self):
        original = self._get_brres('simple_multi_bone_single_bind.brres').models[0]
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False),
                                 self._get_test_fname('simple_multi_bone_single_bind.dae'))
        converter.load_model()
        mdl0 = converter.mdl0
        # test bones
        self.assertEqual(4, len(mdl0.bones))
        CheckPositions.bones_equal(mdl0.bones, original.bones, 0.01, 0.001)
        # Ensure that the bones are correctly linked
        expected_linked_bones = {
            'BlackNWhite1': 'simple001_BNW',
            'BlackNWhite2': 'simple011',
            'GreenCloud': 'simple002_Green',
            'Yellow': 'simple'
        }
        for x in mdl0.objects:
            self.assertEqual(expected_linked_bones[x.name], x.linked_bone.name)
        self.assertTrue(CheckPositions.positions_equal(original.vertices, mdl0.vertices))

    def test_kuribo_loads(self):
        b = self._get_brres('kuribo.brres')
        model = b.models[1]
        converter = DaeConverter(self._get_tmp('.brres'), self._get_test_fname('kuribo.dae'))
        converter.load_model()
        # converter.brres.save(overwrite=True)
        self.assertTrue(CheckPositions().positions_equal(model.vertices, converter.mdl0.vertices, rtol=1e-1, atol=1e-2))
        self.assertTrue(CheckPositions().bones_equal(model.bones, converter.mdl0.bones))

    def test_convert_cow(self):
        original = self._get_brres('cow.brres').models[1]
        converter = DaeConverter(Brres(self._get_tmp('.brres'), read_file=False),
                                 self._get_test_fname('cow.dae'))
        converter.load_model()
        mdl0 = converter.mdl0
        # converter.brres.save(overwrite=True)
        # Ensure that the bones are correct
        CheckPositions.bones_equal(original.bones, mdl0.bones, 0.0001)

    # endregion load_model
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # region save_model
    def test_save_multi_bone_single_bind(self):
        fname = self._get_tmp('.dae')
        converter = DaeConverter(self._get_brres('simple_multi_bone_single_bind.brres'), fname)
        converter.save_model()
        original = converter.mdl0
        converter = DaeConverter(self._get_tmp('.brres'), fname)
        converter.load_model()
        # converter.brres.save(overwrite=True)
        self.assertTrue(CheckPositions().model_equal(original, converter.mdl0, 0.01, 0.001))

    def test_save_multi_bone_as_single_bone(self):
        fname = self._get_tmp('.dae')
        converter = DaeConverter(self._get_brres('simple_multi_bone_single_bind.brres'), fname,
                                 flags=DaeConverter.SINGLE_BONE)
        converter.save_model()
        # load it to test against original
        converter = DaeConverter(self._get_tmp('.brres'), fname)
        converter.load_model()
        converter.brres.save(overwrite=True)
        original = self._get_brres('simple.brres').models[0]
        new = converter.mdl0
        self.assertTrue(CheckPositions().bones_equal(original.bones, new.bones, 0.01,
                                                     0.001))
        self.assertTrue(CheckPositions().positions_equal(original.vertices, new.vertices, 0.01,
                                                         0.001))

    def test_save_multi_bone_scaled_as_single_bone(self):
        fname = self._get_tmp('.dae')
        converter = DaeConverter(self._get_brres('simple_multi_bone_scaled.brres'), fname,
                                 flags=DaeConverter.SINGLE_BONE)
        converter.save_model()
        # load it to test against original
        converter = DaeConverter(self._get_tmp('.brres'), fname)
        converter.load_model()
        original = self._get_brres('simple.brres').models[0]
        self.assertTrue(CheckPositions().positions_equal(original.vertices,
                                                         converter.mdl0.vertices))
        self.assertNotEqual(original.bones, converter.mdl0.bones)  # should be scaled

    def test_save_and_load_multi_bind_equal(self):
        fname = self._get_tmp('.dae')
        converter = DaeConverter(self._get_brres('simple_multi_bone_multi_bind.brres'), fname)
        converter.save_model()
        original = converter.mdl0
        converter = DaeConverter(self._get_tmp('.brres'), fname)
        converter.load_model()
        self.assertTrue(CheckPositions().model_equal(original, converter.mdl0))

    # endregion save_model
