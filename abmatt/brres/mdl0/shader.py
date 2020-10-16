# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from copy import deepcopy, copy

from abmatt.brres.lib.binfile import Folder, PackingError
from abmatt.brres.lib.matching import *
from abmatt.brres.mdl0.wiigraphics.bp import RAS1_IRef, BPCommand, KCel, ColorEnv, AlphaEnv, IndCmd, RAS1_TRef
from autofix import AutoFix, Bug
from abmatt.brres.lib.node import Clipable
from brres.mdl0.stage import Stage


class ShaderList:
    """For maintaining shader collections"""
    FOLDER = "Shaders"

    def __init__(self):
        self.list = {}  # shaders

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def __next__(self):
        return next(self.list)

    def __getitem__(self, item):
        return self.list[item]

    def __setitem__(self, key, value):
        self.list[key] = value

    def updateName(self, old_name, new_name):
        if new_name != old_name:
            shader = self.list.pop(old_name)
            shader.name = new_name
            shader.mark_modified()
            self.list[new_name] = shader

    def getShaders(self, material_list, for_modification=True):
        """Gets the shaders, previously this was used to split shaders but is no longer applicable"""
        return [x.shader for x in material_list]

    def consolidate(self):
        """Creates two lists, one of shaders, and the other a 2d list of the materials they map to"""
        shader_list = []
        material_list = []
        map = self.list
        for name in map:
            found_placement = False
            for i in range(len(shader_list)):
                shader = shader_list[i]
                if map[name] == shader:
                    material_list[i].append(name)
                    found_placement = True
                    break
            if not found_placement:
                shader_list.append(map[name])
                material_list.append([name])
        return shader_list, material_list

    def unpack(self, binfile, materials):
        binfile.recall()  # from offset header
        folder = Folder(binfile, self.FOLDER)
        folder.unpack(binfile)
        list = self.list
        offsets = {}  # for tracking the shaders we've unpacked
        while len(folder.entries):
            name = folder.recallEntryI()
            material = None
            for x in materials:
                if x.name == name:
                    material = x
                    break
            if not material:
                AutoFix.get().info('Removing unlinked shader {}'.format(name))
                continue
            if binfile.offset not in offsets:
                offset_ref = binfile.offset
                d = Shader(name, material, binfile)
                offsets[offset_ref] = d
            else:
                d = deepcopy(offsets[binfile.offset])
                d.name = name
                # d.paste(offsets[binfile.offset], False)
            list[name] = material.shader = d
            # d.material = material
        return offsets

    def pack(self, binfile, folder):
        """Packs the shader data, generating material and index group references"""
        li = self.list
        shaders, names_arr = self.consolidate()
        for i in range(len(shaders)):
            shader = shaders[i]
            names = names_arr[i]
            for name in names:
                folder.createEntryRef(name)  # create index group reference
                try:
                    binfile.createRefFrom(li[name].material.offset)  # create the material shader reference
                except PackingError as e:
                    AutoFix.get().error('Failed to create reference for material {}'.format(name))
                    # raise PackingError(binfile, str(e))
            shader.pack(binfile, i)


class Shader(Clipable):
    BYTESIZE = 512
    SWAP_MASK = BPCommand(0xFE, 0xF)
    SWAP_TABLE = (BPCommand(0xF6, 0x4), BPCommand(0xF7, 0xE), BPCommand(0xF8, 0x0),
                  BPCommand(0xF9, 0xC), BPCommand(0xFA, 0x5), BPCommand(0xFB, 0xD),
                  BPCommand(0xFC, 0xA), BPCommand(0xFD, 0xE))
    SEL_MASK = BPCommand(0xFE, 0xFFFFF0)
    SETTINGS = ('indirectmap', 'indirectcoord', 'stagecount')
    MAP_ID_AUTO = True
    REMOVE_UNUSED_LAYERS = False

    def __init__(self, name, parent, binfile=None):
        self.stages = []
        self.swap_table = deepcopy(self.SWAP_TABLE)
        self.material = parent  # material
        self.indTexMaps = [7] * 4
        self.indTexCoords = [7] * 4
        super(Shader, self).__init__(name, parent, binfile)

    def begin(self):
        self.stages.append(Stage(0, self))

    def __eq__(self, other):
        if len(self.stages) != len(other.stages) or self.getTexRefCount() != other.getTexRefCount():
            return False
        my_stages = self.stages
        others = other.stages
        for i in range(len(my_stages)):
            if my_stages[i] != others[i]:
                return False
        for i in range(len(self.indTexMaps)):
            if self.indTexMaps[i] != other.indTexMaps[i]:
                return False
        for i in range(len(self.indTexCoords)):
            if self.indTexCoords[i] != other.indTexCoords[i]:
                return False
        return True

    # ------------------------------------ CLIPBOARD ----------------------------
    def paste(self, item):
        # doesn't copy swap table
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
        return self.material.name

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level if indentation_level else '>'
        if not key:
            print('{}(Shader){}'.format(trace, self.getMaterialName()))
            indentation_level += 1
            for x in self.stages:
                x.info(key, indentation_level)
        else:
            print('{}(Shader){}: {}:{} '.format(trace, self.getMaterialName(), key, self[key]))

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
        stage['enabled'] = 'false'
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
        if self.material:
            self.material.shaderStages = num_stages

    def onUpdateIndirectStages(self, num_stages):
        self.material.indirectStages = num_stages

    def removeStage(self, id=-1, send_updates=True):
        self.stages.pop(id)
        if send_updates:
            self.onUpdateActiveStages(len(self.stages))
            self.mark_modified()

    def __deepcopy__(self, memodict=None):
        ret = Shader(self.name, self.parent)
        for x in self.stages:
            stage = deepcopy(x)
            stage.parent = ret
            ret.stages.append(ret)
        ret.indTexMaps = copy(self.indTexMaps)
        ret.indTexCoords = copy(self.indTexCoords)
        return ret

    def unpack(self, binfile):
        """ Unpacks shader TEV """
        binfile.start()
        length, outer, id, stage_count, res0, res1, res2, = binfile.read("3I4B", 16)
        layer_indices = binfile.read("8B", 8)
        assert (stage_count <= 16)
        self.stages = []
        for i in range(stage_count):
            self.stages.append(Stage(len(self.stages), self))

        binfile.advance(8)
        kcel = KCel(0)
        tref = RAS1_TRef(0)
        for x in self.swap_table:
            binfile.advance(5)  # skip extra masks
            x.unpack(binfile)
        iref = RAS1_IRef()
        iref.unpack(binfile)
        for i in range(4):
            self.indTexMaps[i] = iref.getTexMap(i)
            self.indTexCoords[i] = iref.getTexCoord(i)
        binfile.align()
        i = 0
        while i < stage_count:
            stage0 = self.stages[i]
            i += 1
            if i < stage_count:
                stage1 = self.stages[i]
                i += 1
            else:
                stage1 = None
            binfile.advance(5)  # skip mask
            kcel.unpack(binfile)
            # print("Color Selection index {}, data {}".format(kcel.getCSel0(), kcel.data))
            # print("Alpha Selection index {}".format(kcel.getASel0()))
            tref.unpack(binfile)
            stage0.map["enabled"] = tref.getTexEnabled0()
            stage0.map["mapid"] = tref.getTexMapID0()
            stage0.map["coordinateid"] = tref.getTexCoordID0()
            stage0.setConstantColorI(kcel.getCSel0(), False)
            stage0.setConstantAlphaI(kcel.getASel0(), False)
            stage0.setRasterColorI(tref.getColorChannel0(), False)
            stage0.unpackColorEnv(binfile)
            if stage1:
                stage1.map["enabled"] = tref.getTexEnabled1()
                stage1.map["mapid"] = tref.getTexMapID1()
                stage1.map["coordinateid"] = tref.getTexCoordID1()
                stage1.setConstantColorI(kcel.getCSel1(), False)
                stage1.setConstantAlphaI(kcel.getASel1(), False)
                stage1.setRasterColorI(tref.getColorChannel1(), False)
                stage1.unpackColorEnv(binfile)
            else:
                binfile.advance(5)  # skip unpack color env
            stage0.unpackAlphaEnv(binfile)
            if stage1:
                stage1.unpackAlphaEnv(binfile)
            else:
                binfile.advance(5)
            stage0.unpackIndirect(binfile)
            if stage1:
                stage1.unpackIndirect(binfile)
            else:
                binfile.advance(5)
            binfile.align(16)
        binfile.advanceAndEnd(self.BYTESIZE)

    def pack(self, binfile, id):
        """ Packs the shader """
        binfile.start()
        binfile.write("IiI4B", self.BYTESIZE, binfile.getOuterOffset(), id,
                      len(self.stages), 0, 0, 0)
        layer_indices = [0xff] * 8
        for i in range(self.getTexRefCount()):
            layer_indices[i] = i
        binfile.write("8B", *layer_indices)
        binfile.align()
        for kcel in self.swap_table:
            self.SWAP_MASK.pack(binfile)
            kcel.pack(binfile)
        # Construct indirect data
        iref = RAS1_IRef()
        data = 0
        for i in range(3, -1, -1):
            data <<= 3
            data |= self.indTexCoords[i] & 7
            data <<= 3
            data |= self.indTexMaps[i] & 7
        iref.data = data
        iref.pack(binfile)
        binfile.align()
        i = j = 0
        while i < len(self.stages):
            stage0 = self.stages[i]
            i += 1
            if i < len(self.stages):
                stage1 = self.stages[i]
                i += 1
            else:
                stage1 = None
            self.SEL_MASK.pack(binfile)
            kcel = KCel(j)  # KCEL
            cc = stage0.getConstantColorI()
            ac = stage0.getConstantAlphaI()
            kcel.data = cc << 4 | ac << 9
            if stage1:
                cc = stage1.getConstantColorI()
                ac = stage1.getConstantAlphaI()
                kcel.data |= cc << 14 | ac << 19
            kcel.pack(binfile)
            # TREF
            tref = RAS1_TRef(j)
            cc = stage0.getRasterColorI()
            tref.data = cc << 7 | stage0["enabled"] << 6 | stage0["coordinateid"] << 3 \
                        | stage0["mapid"]
            if stage1:
                cc = stage1.getRasterColorI()
                tref.data |= cc << 19 | stage1["enabled"] << 18 \
                             | stage1["coordinateid"] << 15 | stage1["mapid"] << 12
            else:
                tref.data |= 0x3bf000
            tref.pack(binfile)
            # all the rest
            stage0.packColorEnv(binfile)
            if stage1:
                stage1.packColorEnv(binfile)
            else:
                binfile.advance(5)
            stage0.packAlphaEnv(binfile)
            if stage1:
                stage1.packAlphaEnv(binfile)
            else:
                binfile.advance(5)
            stage0.packIndirect(binfile)
            if stage1:
                stage1.packIndirect(binfile)
            binfile.align(16)
            j += 1
        binfile.advanceAndEnd(self.BYTESIZE)

    def __str__(self):
        return "shdr layers {} stages {}: {}".format(len(self.stages), self.countDirectStages(),
                                                     self.countIndirectStages())

    def countDirectStages(self):
        i = 0
        for x in self.stages:
            # print("Ref {} is {}".format(i, x))
            if x > 7:
                break
            i += 1
        return i

    def countIndirectStages(self):
        i = 0
        for x in self.indTexCoords:
            if x >= 7:
                break
            i += 1
        return i

    def getIndCoords(self):
        return {x['indirectstage'] for x in self.stages}

    def getTexRefCount(self):
        return len(self.material.layers)

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
            if x.get_str('enabled'):
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
            if self.material.parent.is_map_model:
                b.fix_des = 'Using raster color'
                stage = self.stages[0]
                stage['colora'] = 'rastercolor'
                stage['alphaa'] = 'rasteralpha'
            else:
                b.fix_des = 'Set solid color {}'.format(self.material.getColor(0))
                self.material.set_default_color()
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
                    self.material.removeLayerI(removal_index)
                    b.resolve()
                    resolved_bug = True
                    continue  # don't increment removal index (shift)
            elif x > 1:
                b = Bug(4, 4, '{} Layer {} used {} times by shader.'.format(prefix, i, x), 'check shader')
            removal_index += 1
        ind_matrices_used = self.getIndirectMatricesUsed()
        if resolved_bug:
            self.mark_modified()
        self.material.check_shader(len(self.stages), ind_stage_count, ind_matrices_used)
