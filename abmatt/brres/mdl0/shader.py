# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from copy import deepcopy, copy

from abmatt.autofix import AutoFix, Bug
from abmatt.lib.matching import *
from abmatt.lib.node import Clipable
from abmatt.brres.mdl0.stage import Stage
from abmatt.brres.mdl0.wiigraphics.bp import BPCommand


class Shader(Clipable):
    SWAP_TABLE = (BPCommand(0xF6, 0x4), BPCommand(0xF7, 0xE), BPCommand(0xF8, 0x0),
                  BPCommand(0xF9, 0xC), BPCommand(0xFA, 0x5), BPCommand(0xFB, 0xD),
                  BPCommand(0xFC, 0xA), BPCommand(0xFD, 0xE))
    SETTINGS = ('indirectmap', 'indirectcoord', 'stagecount')
    MAP_ID_AUTO = True
    REMOVE_UNUSED_LAYERS = False

    def __init__(self, name, parent, binfile=None):
        self.stages = []
        self.swap_table = deepcopy(self.SWAP_TABLE)
        # self.material = parent  # material
        self.ind_tex_maps = [7] * 4
        self.ind_tex_coords = [7] * 4
        super(Shader, self).__init__(name, parent, binfile)

    def begin(self):
        self.stages.append(Stage(0, self))

    def __eq__(self, item):
        """
        :type item: Shader
        :return: True if equal
        """
        return self.stages == item.stages and \
               self.swap_table == item.swap_table and \
               it_eq(self.ind_tex_coords, item.ind_tex_coords) and it_eq(self.ind_tex_maps, item.ind_tex_maps)

    def get_colors_used(self):
        colors = set()
        for x in self.stages:
            x.get_colors_used(colors)
        if None in colors:
            colors.remove(None)
        return colors

    # ------------------------------------ CLIPBOARD ----------------------------
    def paste(self, item):
        self.swap_table = deepcopy(item.swap_table)
        num_stages = len(item.stages)
        self.set_stage_count(num_stages)
        for i in range(num_stages):
            self.stages[i].paste(item.stages[i])
        self.ind_tex_coords = [x for x in item.ind_tex_coords]
        self.ind_tex_maps = [x for x in item.ind_tex_maps]
        self.mark_modified()

    def get_indirect_matrices_used(self):
        matrices_used = [False] * 3
        for x in self.stages:
            matrix = x['indirectmatrixselection'][-1]
            if matrix.isdigit():
                matrices_used[int(matrix)] = True
        return matrices_used

    def detect_unused_map_id(self):
        """Attempts to find next available unused mapid"""
        used = [x['mapid'] for x in self.stages]
        for i in range(16):
            if i not in used and i not in self.ind_tex_maps:
                return i
        return 0

    @staticmethod
    def detect_indirect_index(key):
        i = 0 if not key[-1].isdigit() else int(key[-1])
        if not 0 <= i < 4:
            raise ValueError('Indirect index {} out of range (0-3).'.format(i))
        return i

    def __getitem__(self, item):
        return self.get_str(item)

    def __setitem__(self, key, value):
        return self.set_str(key, value)

    def get_str(self, key):
        if self.SETTINGS[0] in key:
            return self.ind_tex_maps
        elif self.SETTINGS[1] in key:
            return self.ind_tex_coords
        elif self.SETTINGS[2] == key:  # stage count
            return len(self.stages)

    def set_str(self, key, value):
        i = value.find(':')
        key2 = 0  # key selection
        if i > -1:
            try:
                key2 = value[:i]
                value = value[i + 1:]
            except IndexError:
                raise ValueError('Argument required after ":"')
        is_single_value = True
        fun = values = None
        try:
            value = validInt(value, 0, 8)
        except ValueError:
            value = parseValStr(value)
            is_single_value = False
            values = [validInt(x) for x in value]
        if self.SETTINGS[0] in key:  # indirect map
            fun = self.set_ind_map
        elif self.SETTINGS[1] in key:  # indirect coord
            fun = self.set_ind_coord
        elif self.SETTINGS[2] == key:  # stage count
            if not is_single_value:
                value = len(values)
            self.set_stage_count(value)
            return
        else:
            raise ValueError('Unknown Key {} for shader'.format(key))
        if is_single_value:
            fun(value, key2)
        else:
            for i in range(len(values)):
                fun(values[i], i)

    def set_ind_coord(self, value, i=0):
        if not 0 <= value < 8:
            raise ValueError('Ind coord {} out of range'.format(value))
        if self.ind_tex_coords[i] != value:
            self.ind_tex_coords[i] = value
            self.on_update_indirect_stages(self.count_ind_stages())
            self.mark_modified()

    def set_ind_map(self, value, i=0):
        if not 0 <= value < 8:
            raise ValueError('Ind map {} out of range'.format(value))
        if self.ind_tex_maps[i] != value:
            self.ind_tex_maps[i] = value
            self.mark_modified()

    def set_stage_count(self, value):
        current_len = len(self.stages)
        if current_len < value:
            while current_len < value:
                self.add_stage(False)
                current_len += 1
        elif current_len > value:
            while current_len > value:
                self.remove_stage(False)
                current_len -= 1
        else:
            return
        self.mark_modified()
        self.on_update_active_stages(value)

    def get_material_name(self):
        return self.parent.name

    def info(self, key=None, indentation_level=0):
        trace = '>' + '  ' * indentation_level if indentation_level else '>'
        if not key:
            AutoFix.info('{}(Shader){}'.format(trace, self.get_material_name()), 1)
            indentation_level += 1
            for x in self.stages:
                x.info(key, indentation_level)
        else:
            AutoFix.info('{}(Shader){}: {}:{} '.format(trace, self.get_material_name(), key, self[key]), 1)

    def get_stage(self, n):
        if not 0 <= n < len(self.stages):
            raise ValueError("Shader stage {} out of range, has {} stages".format(n, len(self.stages)))
        return self.stages[n]

    def set_single_color(self):
        self.set_stage_count(1)
        stage = self.stages[0]
        stage['colora'] = 'color0'
        stage['colorb'] = 'zero'
        stage['colorc'] = 'zero'
        stage['colord'] = 'zero'
        stage['alphaa'] = 'alpha0'
        stage['alphab'] = 'zero'
        stage['alphac'] = 'zero'
        stage['alphad'] = 'zero'
        stage['enabled'] = 'true'
        self.mark_modified()

    def add_stage(self, send_updates=True):
        """Adds stage to shader"""
        stages = self.stages
        s = Stage(len(stages), self)
        mapid = self.detect_unused_map_id()
        s['mapid'] = mapid
        s['coordinateid'] = mapid
        stages.append(s)
        if send_updates:
            self.on_update_active_stages(len(stages))
            self.mark_modified()
        return s

    def on_update_active_stages(self, num_stages):
        if self.parent:
            self.parent.shaderStages = num_stages

    def on_update_indirect_stages(self, num_stages):
        self.parent.indirectStages = num_stages

    def remove_stage(self, id=-1, send_updates=True):
        self.stages.pop(id)
        if send_updates:
            self.on_update_active_stages(len(self.stages))
            self.mark_modified()

    def __deepcopy__(self, memodict=None):
        ret = Shader(self.name, self.parent, True)
        for x in self.stages:
            stage = deepcopy(x, memodict)
            stage.parent = ret
            ret.stages.append(stage)
        ret.ind_tex_maps = copy(self.ind_tex_maps)
        ret.ind_tex_coords = copy(self.ind_tex_coords)
        return ret

    def __str__(self):
        return "shdr stages {}: {}".format(len(self.stages),
                                           self.count_ind_stages())

    def count_ind_stages(self):
        i = 0
        for x in self.ind_tex_coords:
            if x >= 7:
                break
            i += 1
        return i

    def get_ind_coords(self):
        return {x.get_str('indirectstage') for x in self.stages}

    def get_ind_map(self, id=0):
        return self.ind_tex_maps[id]

    def get_ind_coord(self, id=0):
        return self.ind_tex_coords[id]

    def get_tex_ref_count(self):
        return len(self.parent.layers)

    def check(self):
        """Checks the shader for common errors, returns (direct_stage_count, ind_stage_count)"""
        # check stages
        for x in self.stages:
            x.check()
        prefix = 'Shader {}:'.format(self.get_material_name())
        texRefCount = self.get_tex_ref_count()
        tex_usage = [0] * texRefCount
        ind_stage_count = 0
        mark_to_remove = []
        resolved_bug = False
        # direct check
        for x in self.stages:
            if x.get_str('enabled') and x.map_is_used():
                id = x.get_str('mapid')
                if id >= texRefCount:
                    if self.MAP_ID_AUTO:
                        id = self.detect_unused_map_id()
                        b = Bug(2, 2, '{} Stage {} no such layer'.format(prefix, x.name),
                                'Use layer {}'.format(id))
                        if id < texRefCount:
                            x['mapid'] = x['coordinateid'] = id
                            b.resolve()
                            resolved_bug = True
                        else:
                            b.fix_des = 'Remove stage'
                            mark_to_remove.append(x)
                            b.resolve()
                            resolved_bug = True
                else:
                    tex_usage[id] += 1
        for x in mark_to_remove:
            self.stages.remove(x)
        if not self.stages:
            self.set_single_color()
            b = Bug(2, 2, '{} has no stages!'.format(prefix)
                    , None)
            if self.parent.parent.is_map_model:
                b.fix_des = 'Using raster color'
                stage = self.stages[0]
                stage['colora'] = 'rastercolor'
                stage['alphaa'] = 'rasteralpha'
            else:
                self.parent.set_default_color()
                b.fix_des = 'Set solid color {}'.format(self.parent.getColor(0))
            b.resolve()
            resolved_bug = True
        # indirect check
        ind_stages = self.get_ind_coords()
        for stage_id in range(len(self.ind_tex_coords)):
            x = self.ind_tex_coords[stage_id]
            if x < 7:
                if x < texRefCount:
                    try:
                        ind_stages.remove(stage_id)
                        tex_usage[x] += 1
                        ind_stage_count += 1
                    except IndexError:
                        AutoFix.warn('Ind coord {} set but unused'.format(x), 3)
        # now check usage count
        removal_index = 0
        for i in range(len(tex_usage)):
            x = tex_usage[i]
            if x == 0:
                b = Bug(3, 3, '{} Layer {} is not used in shader.'.format(prefix, i), 'remove layer')
                if self.REMOVE_UNUSED_LAYERS:
                    self.parent.remove_layer_i(removal_index)
                    b.resolve()
                    resolved_bug = True
                    continue  # don't increment removal index (shift)
            elif x > 1:
                b = Bug(4, 4, '{} Layer {} used {} times by shader.'.format(prefix, i, x), 'check shader')
            removal_index += 1
        ind_matrices_used = self.get_indirect_matrices_used()
        if resolved_bug:
            self.mark_modified()
        self.parent.check_shader(len(self.stages), ind_stage_count, ind_matrices_used)

