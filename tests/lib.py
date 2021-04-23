import os
import unittest

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.matching import it_eq
from abmatt.converters.geometry import decode_geometry_group


def get_base_path():
    path = new_path = os.path.abspath(__file__)
    fname = None
    while fname != 'abmatt':
        path = new_path
        new_path, fname = os.path.split(path)
    return path


class AbmattTest(unittest.TestCase):
    base_path = get_base_path()
    main_path = os.path.join(base_path, 'abmatt', '__main__.py')

    @classmethod
    def tearDown(cls):
        AutoFix.quit()

    @staticmethod
    def _get_brres_fname(filename):
        return os.path.join(AbmattTest.base_path, 'brres_files', filename)

    @staticmethod
    def _get_test_fname(filename):
        return os.path.join(AbmattTest.base_path, 'test_files', filename)

    @staticmethod
    def _get_tmp(extension):
        return os.path.join(AbmattTest.base_path, 'test_files', 'tmp' + extension)

    @staticmethod
    def _get_brres(filename):
        return Brres(AbmattTest._get_brres_fname(filename))

    @staticmethod
    def _test_mats_equal(materials, updated):
        """A more in depth test for material equality"""
        err = False
        if len(materials) != len(updated):
            print('Lengths different')
            err = True
        for i in range(len(materials)):
            if materials[i] != updated[i]:
                err = True
                my_mat = materials[i]
                updated_mat = updated[i]
                print(my_mat.name + ' not equal to updated ' + updated_mat.name)
                if my_mat.srt0 != updated_mat.srt0:
                    print('SRT0 different')
                if my_mat.pat0 != updated_mat.pat0:
                    print('PAT0 different')
                if my_mat.shader != updated_mat.shader:
                    print('Shader different')
                    stages = my_mat.shader.stages
                    updated_stages = updated_mat.shader.stages
                    for j in range(len(stages)):
                        if stages[j] != updated_stages[j]:
                            print('Stage ' + str(j) + ' different')
                my_lc = my_mat.lightChannels[0]
                up_lc = updated_mat.lightChannels[0]
                if my_lc != up_lc:
                    print('LightChannels different')
                    if my_lc.colorLightControl != up_lc.colorLightControl:
                        print('Color light control diff')
                    if my_lc.alphaLightControl != up_lc.alphaLightControl:
                        print('Alpha light control diff')
                if my_mat.indirect_matrices != updated_mat.indirect_matrices:
                    print('Indirect matrices different')
                if not it_eq(my_mat.colors, updated_mat.colors):
                    print('Shader colors different')
                if not it_eq(my_mat.constant_colors, updated_mat.constant_colors):
                    print('Shader constant colors different')
                if my_mat.ras1_ss != updated_mat.ras1_ss:
                    print('Ras1_ss different')
                my_layers = my_mat.layers
                updated_layers = updated_mat.layers
                if len(my_layers) != len(updated_layers):
                    print('Layers length differ')
                else:
                    for j in range(len(my_layers)):
                        if my_layers[j] != updated_layers[j]:
                            print('Layer ' + my_layers[j].name + ' different from updated ' + updated_layers[j].name)
        return not err


class TestSimple(AbmattTest):
    @classmethod
    def setUpClass(self):
        self.brres = Brres(self._get_brres_fname('simple.brres'))


class TestBeginner(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.brres = Brres(cls._get_brres_fname('beginner_course.brres'))


class CheckPositions:
    @staticmethod
    def __pre_process(vertices1, vertices2):
        if type(vertices1) != list and type(vertices1) != np.array:
            vertices1 = [vertices1]
        if type(vertices2) != list and type(vertices2) != np.array:
            vertices2 = [vertices2]
        mismatched_len = False
        if len(vertices1) != len(vertices2):
            print('Groups are different lengths! {}, {}'.format(len(vertices1), len(vertices2)))
            mismatched_len = True
        return sorted(vertices1, key=lambda x: x.name), sorted(vertices2, key=lambda x: x.name), mismatched_len

    @staticmethod
    def model_equal(mdl1, mdl2, rtol=1.e-5, atol=1.e-8):
        return CheckPositions.bones_equal(mdl1.bones, mdl2.bones, rtol, atol) \
            and CheckPositions.positions_equal(mdl1.vertices, mdl2.vertices, rtol, atol) \
            and CheckPositions.positions_equal(mdl1.uvs, mdl2.uvs, rtol, atol) \
            and CheckPositions.positions_equal(mdl1.normals, mdl2.normals, rtol, atol)

    @staticmethod
    def bones_equal(bone_list1, bone_list2, rtol=1.e-5, atol=1.e-8):
        bone_list1, bone_list2, err = CheckPositions.__pre_process(bone_list1, bone_list2)
        if not err:
            for i in range(len(bone_list1)):
                m1 = bone_list1[i].get_transform_matrix()
                m2 = bone_list2[i].get_transform_matrix()
                if not np.isclose(m1, m2, rtol, atol).all():
                    print('Bone {} and {} have different matrices {}, and {}'.format(bone_list1[i].name,
                                                                                     bone_list2[i].name,
                                                                                     m1, m2))
                    err = True
        return not err

    @staticmethod
    def positions_equal(vertices1, vertices2, rtol=1.e-5, atol=1.e-8):
        """Checks if the vertices are the same"""
        vertices1, vertices2, err = CheckPositions.__pre_process(vertices1, vertices2)
        if not err:
            # Check each vertex group
            for k in range(len(vertices1)):
                points1 = decode_geometry_group(vertices1[k])
                points2 = decode_geometry_group(vertices2[k])
                if points1.shape != points2.shape:
                    print('points {} and {} have different shapes {} and {}'.format(vertices1[k].name,
                                                                                    vertices2[k].name,
                                                                                    points1.shape,
                                                                                    points2.shape))
                    err = True
                    continue
                if not len(points1):
                    continue
                current_err = False
                for i in range(len(points1)):
                    if not np.isclose(points1[i], points2[i], rtol, atol).all():
                        print('Points mismatch at {} Expected {}, found {} '.format(i, points1[i], points2[i]))
                        current_err = err = True
                if current_err:
                    print('{} and {} mismatch'.format(vertices1[k].name, vertices2[k].name))
        return not err
