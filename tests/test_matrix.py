import sys
import unittest

import numpy as np

from abmatt.converters.matrix import srt_to_matrix, matrix_to_srt


class TestMatrix(unittest.TestCase):

    def test_srt_to_matrix(self):
        matrix = np.array([[-0.000000, -0.000000, -1.000000, -2255.436279],
                           [-1.000000, 0.000000, 0.000000, -129.523682],
                           [-0.000000, 1.000000, -0.000000, 1528.046021],
                           [0.000000, 0.000000, 0.000000, 1.000000]])
        converted_matrix = srt_to_matrix((1, 1, 1), (90.0, 0.0, -90.0), (-2255.436, -129.5237, 1528.046))
        self.assertTrue(np.allclose(matrix, converted_matrix, atol=0.0001))

    def test_matrix_to_srt(self):
        s = (1, 1, 1)
        r = (90.0, 0.0, -90.0)
        t = (-2255.436, -129.5237, 1528.046)
        matrix = np.array([[-0.000000, -0.000000, -1.000000, -2255.436279],
                           [-1.000000, 0.000000, 0.000000, -129.523682],
                           [-0.000000, 1.000000, -0.000000, 1528.046021],
                           [0.000000, 0.000000, 0.000000, 1.000000]])
        scale, rotation, translation = matrix_to_srt(matrix)
        self.assertTrue(np.allclose(scale, s, atol=0.0001))
        self.assertTrue(np.allclose(rotation, r, atol=0.0001))
        self.assertTrue(np.allclose(translation, t, atol=0.0001))


if __name__ == '__main__':
    unittest.main()
    sys.exit(0)
