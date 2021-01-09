# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from copy import deepcopy, copy

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.matching import *
from abmatt.brres.lib.node import Clipable
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
        self.indTexMaps = [7] * 4
        self.indTexCoords = [7] * 4
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
               self.indTexCoords == item.indTexCoords and self.indTexMaps == item.indTexMaps

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
        self.indTexCoords = [x for x in item.indTexCoords]
        self.indTexMaps = [x for x in item.indTexMaps]
        self.mark_modified()

    def getIndirectMatricesUsed(self):
        matrices_used = [False] * 3
        for x in self.stages:
            matrix = x['indirectmatrixselection'][-1]
            if matrix.isdigit():
                matrices_used[int(matrix)] = True
        return matrices_used

    def detect_unusedMapId(self):
        """Attempts to find next available unused mapid"""
        used = [x['mapid'] for x in self.stages]
        for i in range(16):
            if i not in used and i not in self.indTexMaps:
                return i
        return 0

    @staticmethod
    def detectIndirectIndex(key):
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
            return self.indTexMaps
        elif self.SETTINGS[1] in key:
            return self.indTexCoords
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
        value = validInt(value, 0, 8)
        if self.SETTINGS[0] in key:  # indirect map
            if self.indTexMaps[key2] != value:
                self.indTexMaps[key2] = value
                self.mark_modified()
        elif self.SETTINGS[1] in key:  # indirect coord
            if self.indTexCoords[key2] != value:
                self.indTexCoords[key2] = value
                self.onUpdateIndirectStages(self.countIndirectStages())
                self.mark_modified()
        elif self.SETTINGS[2] == key:  # stage count
            self.set_stage_count(value)
        else:
            raise ValueError('Unknown Key {} for shader'.format(key))

    def set_stage_count(self, value):
        current_len = len(self.stages)
        if current_len < value:
            while current_len < value:
                self.addStage(False)
                current_len += 1
        elif current_len > value:
            while current_len > value:
                self.removeStage(False)
                current_len -= 1
        else:
            return
        self.mark_modified()
        self.onUpdateActiveStages(value)

    def getMaterialName(self):
        return self.parent.name

    def info(self, key=None, indentation_level=0):
        trace = '>' + '  ' * indentation_level if indentation_level else '>'
        if not key:
            AutoFix.get().info('{}(Shader){}'.format(trace, self.getMaterialName()), 1)
            indentation_level += 1
            for x in self.stages:
                x.info(key, indentation_level)
        else:
            AutoFix.get().info('{}(Shader){}: {}:{} '.format(trace, self.getMaterialName(), key, self[key]), 1)

    def getStage(self, n):
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

    def addStage(self, send_updates=True):
        """Adds stage to shader"""
        stages = self.stages
        s = Stage(len(stages), self)
        mapid = self.detect_unusedMapId()
        s['mapid'] = mapid
        s['coordinateid'] = mapid
        stages.append(s)
        if send_updates:
            self.onUpdateActiveStages(len(stages))
            self.mark_modified()
        return s

    def onUpdateActiveStages(self, num_stages):
        if self.parent:
            self.parent.shaderStages = num_stages

    def onUpdateIndirectStages(self, num_stages):
        self.parent.indirectStages = num_stages

    def removeStage(self, id=-1, send_updates=True):
        self.stages.pop(id)
        if send_updates:
            self.onUpdateActiveStages(len(self.stages))
            self.mark_modified()

    def __deepcopy__(self, memodict=None):
        ret = Shader(self.name, self.parent, True)
        for x in self.stages:
            stage = deepcopy(x, memodict)
            stage.parent = ret
            ret.stages.append(stage)
        ret.indTexMaps = copy(self.indTexMaps)
        ret.indTexCoords = copy(self.indTexCoords)
        return ret

    def __str__(self):
        return "shdr stages {}: {}".format(len(self.stages),
                                                     self.countIndirectStages())

    def countIndirectStages(self):
        i = 0
        for x in self.indTexCoords:
            if x >= 7:
                break
            i += 1
        return i

    def getIndCoords(self):
        return {x.get_str('indirectstage') for x in self.stages}

    def getIndMap(self, id=0):
        return self.indTexMaps[id]

    def getIndCoord(self, id=0):
        return self.indTexCoords[id]

    def setIndCoord(self, value, id=0):
        if not 0 <= value < 8:
            raise ValueError('Ind coord {} out of range'.format(value))
        if value != self.indTexCoords[id]:
            self.indTexCoords[id] = value
            self.mark_modified()

    def setIndMap(self, value, id=0):
        if not 0 <= value < 8:
            raise ValueError('Ind map {} out of range'.format(value))
        if value != self.indTexMaps[id]:
            self.indTexMaps[id] = value
            self.mark_modified()

    def getTexRefCount(self):
        return len(self.parent.layers)

    def check(self):
        """Checks the shader for common errors, returns (direct_stage_count, ind_stage_count)"""
        # check stages
        for x in self.stages:
            x.check()
        prefix = 'Shader {}:'.format(self.getMaterialName())
        texRefCount = self.getTexRefCount()
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
                        id = self.detect_unusedMapId()
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
                b.fix_des = 'Set solid color {}'.format(self.parent.getColor(0))
                self.parent.set_default_color()
            b.resolve()
            resolved_bug = True
        # indirect check
        ind_stages = self.getIndCoords()
        for stage_id in range(len(self.indTexCoords)):
            x = self.indTexCoords[stage_id]
            if x < 7:
                if x < texRefCount:
                    try:
                        ind_stages.remove(stage_id)
                        tex_usage[x] += 1
                        ind_stage_count += 1
                    except IndexError:
                        AutoFix.get().warn('Ind coord {} set but unused'.format(x), 3)
        # now check usage count
        removal_index = 0
        for i in range(len(tex_usage)):
            x = tex_usage[i]
            if x == 0:
                b = Bug(3, 3, '{} Layer {} is not used in shader.'.format(prefix, i), 'remove layer')
                if self.REMOVE_UNUSED_LAYERS:
                    self.parent.removeLayerI(removal_index)
                    b.resolve()
                    resolved_bug = True
                    continue  # don't increment removal index (shift)
            elif x > 1:
                b = Bug(4, 4, '{} Layer {} used {} times by shader.'.format(prefix, i, x), 'check shader')
            removal_index += 1
        ind_matrices_used = self.getIndirectMatricesUsed()
        if resolved_bug:
            self.mark_modified()
        self.parent.check_shader(len(self.stages), ind_stage_count, ind_matrices_used)

# Old code for maintaining shaders
# class ShaderList:
#     """For maintaining shader collections"""
#     FOLDER = "Shaders"
#
#     def __init__(self):
#         self.list = {}  # shaders
#
#     def __len__(self):
#         return len(self.list)
#
#     def __iter__(self):
#         return iter(self.list)
#
#     def __next__(self):
#         return next(self.list)
#
#     def __getitem__(self, item):
#         return self.list[item]
#
#     def __setitem__(self, key, value):
#         self.list[key] = value
#
#     def updateName(self, old_name, new_name):
#         if new_name != old_name:
#             shader = self.list.pop(old_name)
#             shader.name = new_name
#             shader.mark_modified()
#             self.list[new_name] = shader
#
#     def getShaders(self, material_list, for_modification=True):
#         """Gets the shaders, previously this was used to split shaders but is no longer applicable"""
#         return [x.shader for x in material_list]
#
#     def consolidate(self):
#         """Creates two lists, one of shaders, and the other a 2d list of the materials they map to"""
#         shader_list = []
#         material_list = []
#         map = self.list
#         for name in map:
#             found_placement = False
#             for i in range(len(shader_list)):
#                 shader = shader_list[i]
#                 if map[name] == shader:
#                     material_list[i].append(name)
#                     found_placement = True
#                     break
#             if not found_placement:
#                 shader_list.append(map[name])
#                 material_list.append([name])
#         return shader_list, material_list
#
#     def unpack(self, binfile, materials):
#         binfile.recall()  # from offset header
#         folder = Folder(binfile, self.FOLDER)
#         folder.unpack(binfile)
#         list = self.list
#         offsets = {}  # for tracking the shaders we've unpacked
#         while len(folder.entries):
#             name = folder.recallEntryI()
#             material = None
#             for x in materials:
#                 if x.name == name:
#                     material = x
#                     break
#             if not material:
#                 AutoFix.get().info('Removing unlinked shader {}'.format(name))
#                 continue
#             if binfile.offset not in offsets:
#                 offset_ref = binfile.offset
#                 d = Shader(name, material, binfile)
#                 offsets[offset_ref] = d
#             else:
#                 d = deepcopy(offsets[binfile.offset])
#                 d.name = name
#                 # d.paste(offsets[binfile.offset], False)
#             list[name] = material.shader = d
#             # d.material = material
#         return offsets
#
#     def pack(self, binfile, folder):
#         """Packs the shader data, generating material and index group references"""
#         li = self.list
#         shaders, names_arr = self.consolidate()
#         for i in range(len(shaders)):
#             shader = shaders[i]
#             names = names_arr[i]
#             for name in names:
#                 folder.createEntryRef(name)  # create index group reference
#                 try:
#                     binfile.createRefFrom(li[name].material.offset)  # create the material shader reference
#                 except PackingError as e:
#                     AutoFix.get().error('Failed to create reference for material {}'.format(name))
#                     # raise PackingError(binfile, str(e))
#             shader.pack(binfile, i)
