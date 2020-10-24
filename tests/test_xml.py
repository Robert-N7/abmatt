import unittest

from converters.xml import XML


class MyTestCase(unittest.TestCase):

    def test_something(self):
        root = XML('../test_files/3ds_simple.DAE').root
        self.assertEqual(root.tag, 'COLLADA')
        self.assertTrue(root.children)


if __name__ == '__main__':
    unittest.main()
