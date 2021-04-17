import os
import unittest

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.matching import it_eq


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
    def _get_brres(filename):
        return Brres(AbmattTest._get_brres_fname(filename))


class TestSimple(AbmattTest):
    @classmethod
    def setUpClass(self):
        self.brres = Brres(self._get_brres_fname('simple.brres'))


class TestBeginner(AbmattTest):
    @classmethod
    def setUpClass(cls):
        cls.brres = Brres(cls._get_brres_fname('beginner_course.brres'))


def test_mats_equal(materials, updated):
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
