import os
import unittest

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib import matching
from abmatt.brres.lib.matching import it_eq
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.mdl0.polygon import Polygon
from abmatt.brres.mdl0.shader import Shader


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
    def setUpClass(cls):
        AutoFix.set_loudness('2')

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
    def _get_tmp(extension='.brres', remove_if_exists=True):
        if not extension.startswith('.'):
            extension = '.' + extension
        f = os.path.join(AbmattTest.base_path, 'test_files', 'tmp' + extension)
        if remove_if_exists and os.path.exists(f):
            os.remove(f)
        return f

    @staticmethod
    def _get_brres(filename):
        if not filename.endswith('.brres'):
            filename += '.brres'
        return Brres(AbmattTest._get_brres_fname(filename))

    @staticmethod
    def _test_mats_equal(materials, updated, sort=False):
        """A more in depth test for material equality"""
        err = False
        if len(materials) != len(updated):
            print('Lengths different')
            err = True
        if sort:
            materials = sorted(materials, key=lambda x: x.name)
            updated = sorted(materials, key=lambda x: x.name)
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
                            if my_layers[j].minfilter != updated_layers[j].minfilter:
                                print('Minfilter different')
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
    def __pre_process(vertices1, vertices2, group_type):
        if vertices1 is None or vertices2 is None:
            if vertices1 is not None or vertices2 is not None:
                print(f'{vertices1} != {vertices2}')
                return vertices1, vertices2, True
            return vertices1, vertices2, False
        if type(vertices1) != list and type(vertices1) != np.array:
            vertices1 = [vertices1]
        if type(vertices2) != list and type(vertices2) != np.array:
            vertices2 = [vertices2]
        mismatched_len = False
        if len(vertices1) != len(vertices2):
            print('{} Groups are different lengths! {}, {}'.format(group_type, len(vertices1), len(vertices2)))
            mismatched_len = True
        if len(vertices1) == 0:
            return vertices1, vertices2, mismatched_len
        # Try to sort by name
        v1 = sorted(vertices1, key=lambda x: x.name)
        v2 = sorted(vertices2, key=lambda x: x.name)
        if not matching.fuzzy_match(v1[0].name, v2):  # no match! try matching shapes
            # print('Groups dont have matching names!')
            v1 = sorted(vertices1, key=lambda x: x.count)
            v2 = sorted(vertices2, key=lambda x: x.count)

        return v1, v2, mismatched_len

    @staticmethod
    def polygons_equal(poly1, poly2, rtol=-1.e-2, atol=1.e-3):
        p1, p2, err = CheckPositions.__pre_process(poly1, poly2, 'polygons')
        if not err:
            for i in range(len(p1)):
                t1 = p1[i]
                t2 = p2[i]
                n1 = t1.get_normal_group()
                n2 = t2.get_normal_group()
                if not (CheckPositions.bones_equal(t1.get_linked_bone(), t2.get_linked_bone(), rtol, atol) and
                        CheckPositions.positions_equal(t1.get_vertex_group(), t2.get_vertex_group(), rtol, atol,
                                                       group_name='vertices') and
                        (not n1 or not n2 or CheckPositions.positions_equal(n1, n2,
                                                       group_name='normals')) and
                        all(CheckPositions.positions_equal(t1.get_uv_group(x), t2.get_uv_group(x), rtol, atol,
                                                           group_name='uvs')
                            for x in range(8))
                        and CheckPositions.colors_equal(t1.get_color_group(), t2.get_color_group())):
                    print(f'polygons {t1.name} != {t2.name}')
                    err = True
        return not err



    @staticmethod
    def colors_equal(colr1, colr2, rtol=1.e-2, atol=1.e-3):
        c1, c2, err = CheckPositions.__pre_process(colr1, colr2, 'colors')
        if not c1 or not c2:
            return not err
        if not err:
            for i in range(len(c1)):
                colr1 = c1[i]
                colr2 = c2[i]
                if colr1.format != colr2.format:
                    print('Colors {}, {} have mismatching formats'.format(colr1.name, colr2.name))
                decoded_c1 = colr1.get_decoded()
                decoded_c2 = colr2.get_decoded()
                if len(decoded_c1) != len(decoded_c2):
                    print('Colors {}, {} dont have matching lengths!'.format(colr1.name, colr2.name))
                if len(decoded_c1) != colr1.count:
                    print('Color {} length does not match count!'.format(colr1.name))
                if len(decoded_c2) != colr2.count:
                    print('Color {} length does not match count!'.format(colr2.name))
                decoded_c2 = sorted(decoded_c2, key=lambda x: tuple(x))
                decoded_c1 = sorted(decoded_c1, key=lambda x: tuple(x))
                current_err = False
                for j in range(min(len(decoded_c2), len(decoded_c1))):
                    if not np.isclose(decoded_c1[j], decoded_c2[j], rtol, atol).all():
                        print('Colors mismatch at {}, Expected {} found {}'.format(j, decoded_c1[j], decoded_c2[j]))
                        current_err = err = True
                if current_err:
                    print('Colors {}, {} mismatch'.format(colr1.name, colr2.name))
        return not err

    @staticmethod
    def model_equal(mdl1, mdl2, rtol=1.e-2, atol=1.e-3):
        return CheckPositions.polygons_equal(mdl1.objects, mdl2.objects, rtol, atol)

    @staticmethod
    def bones_equal(bone_list1, bone_list2, rtol=1.e-2, atol=1.e-3):
        bone_list1, bone_list2, err = CheckPositions.__pre_process(bone_list1, bone_list2, 'bones')
        if not err and bone_list1 is not None:
            for i in range(len(bone_list1)):
                b1 = bone_list1[i]
                b2 = bone_list2[i]
                m1 = b1.get_transform_matrix()
                m2 = b2.get_transform_matrix()
                if not np.isclose(m1, m2, rtol, atol).all():
                    print('Bone have different matrices {}\n{}\n{}\n{}\n'.format(b1.name, m1, b2.name, m2))
                    err = True
                srt1 = [b1.scale, [x % 360 for x in b1.rotation], b1.translation]
                srt2 = [b2.scale, [x % 360 for x in b1.rotation], b2.translation]
                if not np.isclose(srt1, srt2, rtol, atol).all():
                    print('Bone have different srt {}\n{}\n{}\n{}\n'.format(b1.name, srt1, b2.name, srt2))
                    err = True
                if b1.b_parent or b2.b_parent:
                    if b1.b_parent.name != b2.b_parent.name:
                        print('Bones {}, {} have different parents {}, {}'.format(b1.name, b2.name,
                                                                                  b1.b_parent.name, b2.b_parent.name))
                        err = True
        return not err

    @staticmethod
    def pos_eq_helper(points1, points2, v1_name, v2_name, rtol, atol, err_points):
        if points1.shape != points2.shape:
            print('points {} and {} have different shapes {} and {}'.format(v1_name,
                                                                            v2_name,
                                                                            points1.shape,
                                                                            points2.shape))
            return False
        if not len(points1):
            return True
        current_err = False
        for i in range(len(points1)):
            if not np.isclose(points1[i], points2[i], rtol, atol).all():
                err_points.append(i)
                current_err = True
        return not current_err

    @staticmethod
    def positions_equal(vertices1, vertices2, rtol=1.e-2, atol=1.e-3, group_name='points'):
        """Checks if the vertices are the same"""
        vertices1, vertices2, err = CheckPositions.__pre_process(vertices1, vertices2, group_name)
        if not vertices1 or not vertices2:
            return not err
        if not err:
            # Check each vertex group
            for k in range(len(vertices1)):
                v1_decoded = vertices1[k].get_decoded()
                v2_decoded = vertices2[k].get_decoded()
                points1 = np.array(sorted(v1_decoded, key=lambda x: tuple(np.around(x, 2))))
                points2 = np.array(sorted(v2_decoded, key=lambda x: tuple(np.around(x, 2))))
                errs = []
                current_err = False
                if not CheckPositions.pos_eq_helper(points1, points2, vertices1[k].name, vertices2[k].name,
                                                    rtol, atol, errs):
                    if errs:
                        p1 = np.array(sorted([points1[z] for z in errs], key=lambda x: tuple(x)))
                        p2 = np.array(sorted([points2[z] for z in errs], key=lambda x: tuple(x)))
                        if CheckPositions.pos_eq_helper(p1, p2,
                                                     vertices1[k].name, vertices2[k].name, rtol, atol, []):
                            continue
                    for x in errs:
                        print('Points mismatch at {} Expected {}, found {} '.format(x, points1[x], points2[x]))

                    err = current_err = True
                if current_err:
                    print('{} and {} mismatch'.format(vertices1[k].name, vertices2[k].name))
        return not err


class CheckAttr:
    def __init__(self, attr, sub_check_attr=None):
        """
        :param attr the attribute to check
        :param sub_check_attr list of CheckAttr to use as a subcheck
        """
        self.attr = attr
        self.sub_check_attr = sub_check_attr


class CheckNodeEq:

    def __init__(self, node, other, check_attr=[], trace=True, parent_node=None):
        self.node = node
        self.other = other
        self.result = it_eq(node, other)
        self.my_item_diff = self.their_item_diff = self.attr = None
        self.err_message = ''
        self.check_attr = check_attr
        self.parent_node = parent_node if parent_node else self
        if trace:
            self.err_trace = self.trace()

    def __str__(self):
        if self.result:
            return self.err_message
        return self.get_err()

    def get_err(self):
        mine, theirs = self.err_trace
        return self.parent_node.err_message + f'\nMINE: {mine}\nTHEIRS: {theirs}\n'

    def trace(self, my_trace='', other_trace=''):
        if self.result:
            self.err_message = 'Items equal, errors found'
            return None, None
        my_trace = str(self.node) if not my_trace else my_trace + '->' + str(self.node)
        other_trace = str(self.other) if not other_trace else other_trace + '->' + str(self.other)
        if self.check_attr:
            for check in self.check_attr:
                if type(check) == str:
                    check = CheckAttr(check)
                self.parent_node.attr = check.attr
                mine = getattr(self.node, check.attr)
                theirs = getattr(self.other, check.attr)
                if mine is None or theirs is None:
                    if mine is not theirs:
                        self.parent_node.err_message = f'Null {check.attr}! ({mine} != {theirs})'
                        break
                    continue
                if type(mine) not in (list, dict, set, tuple):
                    mine_sub, their_sub = CheckNodeEq(mine, theirs,
                                                      check.sub_check_attr,
                                                      False,
                                                      self.parent_node).trace(my_trace, other_trace)
                    if mine_sub or their_sub:
                        return mine_sub, their_sub
                else:  # iterable?
                    if len(mine) != len(theirs):
                        self.parent_node.err_message = f'{check.attr} has mismatching lengths!'
                        break
                    if type(mine) == dict:
                        for key in mine:
                            if key not in theirs:
                                self.parent_node.err_message = f'{check.attr} missing item {key} in theirs!'
                                break
                            mine_sub, their_sub = CheckNodeEq(mine[key], theirs[key],
                                                              check.sub_check_attr,
                                                              False,
                                                              self.parent_node).trace(my_trace, other_trace)
                            if mine_sub or their_sub:
                                return mine_sub, their_sub
                    else:
                        for i in range(len(mine)):
                            mine_sub, their_sub = CheckNodeEq(mine[i], theirs[i],
                                                              check.sub_check_attr,
                                                              False,
                                                              self.parent_node).trace(my_trace, other_trace)
                            if mine_sub or their_sub:
                                return mine_sub, their_sub
            self.parent_node.attr = None
        self.parent_node.my_item_diff = self.node
        self.parent_node.their_item_diff = self.other
        self.parent_node.err_message += f'\nERR checking {self.parent_node.attr}\n({self.node} != {self.other})'
        return my_trace, other_trace


class CheckMaterialAttr(CheckAttr):
    class CheckLayerAttr(CheckAttr):
        def __init__(self):
            sub_attrs = ['enable', 'scale', 'rotation', 'translation', 'scn0_light_ref', 'scn0_camera_ref',
                         'map_mode', 'vwrap', 'uwrap', 'minfilter', 'magfilter', 'lod_bias', 'max_anisotrophy',
                         'texel_interpolate', 'clamp_bias', 'normalize', 'projection', 'inputform', 'type',
                         'coordinates', 'emboss_source', 'emboss_light']
            super().__init__('layers', sub_attrs)

    class CheckPat0Attr(CheckAttr):
        def __init__(self):
            super().__init__('pat0')

    class CheckSrt0Attr(CheckAttr):
        def __init__(self):
            super().__init__('srt0')

    class CheckShaderAttr(CheckAttr):
        def __init__(self):
            sub_attrs = ['swap_table', 'ind_tex_maps', 'ind_tex_coords',
                         CheckMaterialAttr.CheckStageAttr()]
            super().__init__('shader', sub_attrs)

    class CheckStageAttr(CheckAttr):
        def __init__(self):
            sub_attrs = ['map_id', 'coord_id', 'texture_swap_sel', 'raster_color', 'raster_swap_sel',
                         'constant', 'sel_a', 'sel_b', 'sel_c', 'sel_d', 'bias', 'oper', 'clamp', 'scale', 'dest',
                         'constant_a', 'sel_a_a', 'sel_b_a', 'sel_c_a', 'sel_d_a',
                         'bias_a', 'oper_a', 'clamp_a', 'scale_a', 'dest_a',
                         'ind_stage', 'ind_format', 'ind_alpha', 'ind_bias', 'ind_matrix',
                         'ind_s_wrap', 'ind_t_wrap', 'ind_use_prev', 'ind_unmodify_lod']
            super().__init__('stages', sub_attrs)

    def __init__(self):
        sub_attrs = [self.CheckShaderAttr(), self.CheckLayerAttr(), self.CheckPat0Attr(), self.CheckSrt0Attr(),
                     CheckAttr('colors'), CheckAttr('constant_colors'),
                     CheckAttr('indirect_matrices'), CheckAttr('lightChannels'),
                     CheckAttr('blend_dest'), CheckAttr('blend_source'), CheckAttr('blend_logic'),
                     CheckAttr('blend_subtract'), CheckAttr('blend_update_alpha'), CheckAttr('blend_update_color'),
                     CheckAttr('blend_dither'), CheckAttr('blend_logic_enabled'), CheckAttr('blend_enabled'),
                     CheckAttr('depth_function'), CheckAttr('depth_update'), CheckAttr('depth_test'),
                     CheckAttr('logic'), CheckAttr('comp1'), CheckAttr('comp0'), CheckAttr('ref1'), CheckAttr('ref0'),
                     CheckAttr('constant_alpha_enabled'), CheckAttr('constant_alpha'),
                     CheckAttr('indirect_matrices')]
        super().__init__('material', sub_attrs)


class CheckPolysAttr(CheckAttr):
    def __init__(self):
        sub_attrs = [CheckMaterialAttr()]
        super().__init__('objects', sub_attrs)


class CheckModelsAttr(CheckAttr):
    def __init__(self):
        sub_attrs = [CheckPolysAttr()]
        super().__init__('models', sub_attrs)


class CheckBrresAttr(CheckAttr):
    def __init__(self):
        sub_attrs = [CheckModelsAttr(), CheckTextureMap(), CheckAttr('unused_pat0'),
                     CheckAttr('unused_srt0'),
                     CheckAttr('chr0'),
                     CheckAttr('scn0'),
                     CheckAttr('shp0'),
                     CheckAttr('clr0')]
        super().__init__('brres', sub_attrs)


class CheckTextureMap(CheckAttr):
    def __init__(self):
        super().__init__('texture_map')


CHECK_ATTR_MAP = {
    Brres: CheckBrresAttr,
    Mdl0: CheckModelsAttr,
    Polygon: CheckPolysAttr,
    Material: CheckMaterialAttr,
}


def brres_eq(mine, other):
    check = CheckNodeEq(mine, other, [CheckModelsAttr(),
                                      CheckTextureMap(),
                                      CheckAttr('unused_pat0'),
                                      CheckAttr('unused_srt0'),
                                      CheckAttr('chr0'),
                                      CheckAttr('scn0'),
                                      CheckAttr('shp0'),
                                      CheckAttr('clr0')])
    if not check.result:
        print(check)
    return check.result


def node_eq(mine, other):
    if type(mine) in (list, tuple):
        if len(mine) != len(other):
            print('Mismatching lengths!')
        else:
            for i in range(len(mine)):
                if not node_eq(mine[i], other[i]):
                    return False
    else:
        check_attr = CHECK_ATTR_MAP[type(mine)]
        check = CheckNodeEq(mine, other, check_attr().sub_check_attr)
        if not check.result:
            print(check)
        return check.result
    return True