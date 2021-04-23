from abmatt.brres import Brres
from abmatt.converters.convert_dae import DaeConverter2
from tests.lib import AbmattTest, CheckPositions


class DaeConverterTest(AbmattTest):
    # ------------------------------------------------------
    # region load_model
    def test_convert_to_correct_position(self):
        # Get reference to beginner_course to test against
        beginner_brres = self._get_brres('beginner_course.brres')
        original_vertices = beginner_brres.models[0].vertices
        # Convert dae
        brres = Brres(self._get_tmp('.brres'), readFile=False)
        dae = self._get_test_fname('beginner.dae')
        converter = DaeConverter2(brres, dae)
        converter.load_model()
        new_vertices = brres.models[0].vertices
        self.assertTrue(CheckPositions().positions_equal(original_vertices, new_vertices))

    def test_convert_with_json(self):
        brres = self._get_brres('beginner_course.brres')
        dae_file = self._get_test_fname('beginner.dae')
        converter = DaeConverter2(Brres(self._get_tmp('.brres'), readFile=False), dae_file)
        converter.load_model()
        self._test_mats_equal(converter.brres.models[0].materials, brres.models[0].materials)

    def test_convert_multi_material_geometry(self):
        """Tests converting dae file that has multiple materials associated with geometry"""
        converter = DaeConverter2(Brres(self._get_tmp('.brres'), readFile=False), self._get_test_fname('blender.dae'))
        converter.load_model()
        mdl0 = converter.brres.models[0]
        self.assertEqual(len(mdl0.materials), 2)
        self.assertEqual(len(mdl0.objects), 2)

    def test_convert_single_bone(self):
        original = self._get_brres('simple.brres')
        converter = DaeConverter2(Brres(self._get_tmp('.brres'), readFile=False),
                                  self._get_test_fname('simple_multi_bone.dae'),
                                  flags=DaeConverter2.SINGLE_BONE)
        converter.load_model()
        mdl0 = converter.mdl0
        # Test single bone
        self.assertEqual(len(mdl0.bones), 1)
        # Test positions
        self.assertTrue(CheckPositions.positions_equal(original.models[0].vertices, mdl0.vertices))

    def test_convert_multi_bone(self):
        original = Brres(self._get_test_fname('tmp_BB.brres'))
        converter = DaeConverter2(Brres(self._get_tmp('.brres'), readFile=False),
                                  self._get_test_fname('simple_multi_bone.dae'))
        converter.load_model()
        mdl0 = converter.mdl0
        self.assertEqual(4, len(mdl0.bones))
        converter.brres.save(overwrite=True)
        # Ensure that the bones are correctly linked
        expected_linked_bones = {
            'BlackNWhite1': 'simple001_BNW',
            'BlackNWhite2': 'simple011',
            'GreenCloud': 'simple002_Green',
            'Yellow': 'simple'
        }
        for x in mdl0.objects:
            self.assertEqual(expected_linked_bones[x.name], x.bone.name)
        self.assertTrue(CheckPositions.positions_equal(original.models[0].vertices, mdl0.vertices))

    # endregion load_model
    # ------------------------------------------------------------------
