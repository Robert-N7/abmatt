import unittest
import numpy as np

from tests.lib import TestSimple, TestWater
from abmatt.converters.matrix import srt_to_matrix, matrix_to_srt


class TestMatrix(TestWater):

    def test_srt_to_matrix(self):
        bone = self.brres.models[0].bones[0]
        transform_matrix = np.array(bone.get_transform_matrix())
        converted_matrix = srt_to_matrix(bone.scale, bone.rotation, bone.translation)
        self.assertTrue(np.allclose(transform_matrix, converted_matrix))

    def test_matrix_to_srt(self):
        bone = self.brres.models[0].bones[0]
        transform_matrix = np.array(bone.get_transform_matrix())
        scale, rotation, translation = matrix_to_srt(transform_matrix)
        self.assertTrue(np.allclose(scale, bone.scale))
        self.assertTrue(np.allclose(rotation, bone.rotation))
        self.assertTrue(np.allclose(translation, bone.translation))




if __name__ == '__main__':
    unittest.main()
