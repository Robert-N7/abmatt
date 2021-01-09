import os
import sys
import unittest

from abmatt.brres import Brres


class MyTestCase(unittest.TestCase):
    def test_brres_open_close(self):
        b = Brres('../brres_files/beginner_course.brres')
        self.assertEqual(len(b.models), 1)
        self.assertEqual(len(b.textures), 29)
        self.assertEqual(len(b.pat0), 1)
        self.assertEqual(len(b.srt0), 1)
        test_file = '../brres_files/test.brres'
        if os.path.exists(test_file):
            os.remove(test_file)
        b.save(test_file, True)
        self.assertTrue(os.path.exists(test_file))

if __name__ == '__main__':
    unittest.main()
    sys.exit(0)
