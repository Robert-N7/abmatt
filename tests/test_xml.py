import unittest

from converters.xml import read_xml


class MyTestCase(unittest.TestCase):

    def test_something(self):
        root = read_xml('../test_files/3ds_bll.DAE')
        self.assertEqual(root.tag, 'COLLADA')
        self.assertTrue(root.children)


if __name__ == '__main__':
    unittest.main()
