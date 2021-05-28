import struct

from abmatt.autofix import AutoFix
from abmatt.lib.binfile import UnpackingError
from debug.analyze import gather_files
from tests.kmp.lib.test_pack import TestPack


class TestKmp(TestPack):
    def test_all_eq(self):
        errors = 0
        # Known errors with different version files
        # old_koopa_gba has a different camera index out of range 0xfb != 0xff
        ignore = ['old_koopa_gba', 'old_mario_gc_', 'draw_demo', 'loser_demo']
        AutoFix.set_loudness('0')
        for x in gather_files(self.base_path, filter='.kmp'):
            try:

                self._test_pack_eq(x)
            except (struct.error, UnpackingError, AssertionError, ValueError) as e:
                ignore_it = False
                for ig in ignore:
                    if ig in x:
                        ignore_it = True
                        break
                if not ignore_it:
                    print(f'{x} error {e}')
                    errors += 1
        self.assertEqual(0, errors)

