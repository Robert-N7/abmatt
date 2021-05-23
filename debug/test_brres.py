import os
import unittest

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.converters.convert_dae import DaeConverter
from abmatt.converters.convert_obj import ObjConverter
from debug.analyze import gather_files, get_project_root


class TestBrres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = get_project_root()
        AutoFix.set_loudness('0')

    def tearDown(self):
        try:
            os.remove(self.tmp)
        except (AttributeError, FileNotFoundError):
            pass

    def _get_tmp(self, ext='.brres'):
        self.tmp = os.path.join(self.root, 'tmp' + ext)
        return self.tmp

    def test_save_all(self):
        tmp = self._get_tmp()
        for x in gather_files(self.root):
            try:
                original = Brres(x)
                original.save(tmp, overwrite=True)
                new = Brres(tmp)
                self.assertEqual(original, new)
            except:
                print(f'ERROR saving {x}')
                raise

    def test_export_all_dae(self):
        tmp = self._get_tmp('.dae')
        for x in gather_files(self.root):
            try:
                converter = DaeConverter(Brres(x), tmp)
                for model in converter.brres.models:
                    converter.save_model(model)
            except:
                print(f'ERROR exporting {x}')
                raise

    def test_export_all_obj(self):
        tmp = self._get_tmp('.obj')
        for x in gather_files(self.root):
            try:
                converter = ObjConverter(Brres(x), tmp)
                for model in converter.brres.models:
                    converter.save_model(model)
            except:
                print(f'ERROR exporting {x}')
                raise

    def test_import_all_dae(self):
        tmp = self._get_tmp()
        for x in gather_files(self.root, filter='.dae'):
            try:
                converter = DaeConverter(tmp, x)
                converter.load_model()
                converter.brres.save(overwrite=True)
            except:
                print(f'ERROR importing {x}')
                raise

    def test_import_all_obj(self):
        tmp = self._get_tmp()
        for x in gather_files(self.root, filter='.obj'):
            try:
                converter = ObjConverter(tmp, x)
                converter.load_model()
                converter.brres.save(overwrite=True)
            except:
                print(f'ERROR importing {x}')
                raise

if __name__ == '__main__':
    unittest.main()
