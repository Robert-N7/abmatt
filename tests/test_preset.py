import os

from abmatt.command import load_preset_file
from abmatt.converters.convert_dae import DaeConverter
from abmatt.converters.convert_lib import Converter
from tests.lib import AbmattTest


class TestPreset(AbmattTest):
    @classmethod
    def setUpClass(cls):
        load_preset_file(os.path.join(cls.base_path, 'test_files'))
        Converter.ENCODE_PRESET = 'load_preset'

    def test_convert_loads_presets(self):
        converter = DaeConverter(self._get_tmp('.brres'), self._get_test_fname('3ds_simple.DAE'), encode=True).convert()
        self.assertTrue(all([mat.blend_enabled for mat in converter.mdl0.materials]))

    def test_replace_doesnt_load_preset(self):
        Converter.ENCODE_PRESET_ON_NEW = True
        converter = DaeConverter(self._get_brres('simple.brres'), self._get_test_fname('3ds_simple.DAE'),
                                 encode=True).convert()
        converter.brres.save(self._get_tmp('.brres'))   # save so we don't overwrite accidentally
        self.assertFalse(all([x.blend_enabled for x in converter.mdl0.materials]))
