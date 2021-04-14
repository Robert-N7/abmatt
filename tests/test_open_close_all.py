import os
import sys
import unittest

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from tests.lib import AbmattTest


class TestOpenCloseAll(AbmattTest):
    def test_open_close(self):
        dir = os.path.join(self.base_path, 'brres_files')
        output = os.path.join(dir, 'test.brres')
        for x in os.listdir(dir):
            current_file = os.path.join(dir, x)
            if current_file != output:
                if os.path.exists(output):
                    os.remove(output)
                if x.endswith('.brres'):
                    b = Brres(current_file)
                    b.save(output, True)
                self.assertTrue(os.path.exists(output))
        return True


if __name__ == '__main__':
    unittest.main()

