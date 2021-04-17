from abmatt.brres.mdl0.material.material import Material
import json

from abmatt.brres.pat0.pat0_material import Pat0MatAnimation
from abmatt.brres.srt0.srt0_animation import SRTKeyFrameList


class MatsToJsonConverter:
    """Converts materials to text"""

    class MatToJsonError(Exception):
        pass

    def __init__(self, filename):
        """
        :param filename: file to load from/export to
        """
        self.filename = filename
        self.materials_by_name = {}

    def export(self, materials):
        """ Exports the materials to a JSON file
        :param materials: List of Brres Materials
        :return: dictionary object of material names to their data
        """
        for x in materials:
            self.materials_by_name[x.name] = self.__get_material_str(x)
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.materials_by_name, indent=3))
        return self.materials_by_name

    def load(self):
        """Loads the json file
        :returns materials loaded
        """
        with open(self.filename, 'r') as f:
            self.materials_by_name = json.loads(f.read())
        materials = [self.__load_material(Material(x), self.materials_by_name[x])
                          for x in self.materials_by_name]
        return materials

    def load_into(self, materials):
        """ Loads json data into materials, if the material name isn't found it is ignored
        :param materials: the materials to load data into
        :return: materials
        """
        with open(self.filename, 'r') as f:
            self.materials_by_name = json.loads(f.read())
        for x in materials:
            data = self.materials_by_name.get(x.name)
            if data:
                self.__load_material(x, data)

    def __load_material(self, material, data):
        self.__load_settings(material, data.get('settings'))
        data_layers = data.get('layers')
        if data_layers:
            self.__load_layers(material.layers, data_layers)
        data_shader = data.get('shader')
        if data_shader:
            self.__load_shader(material.shader, data_shader)
        srt0_data = data.get('srt0')
        if srt0_data is not None:
            material.add_srt0()
            self.__load_srt0(material.srt0, srt0_data)
        pat0_data = data.get('pat0')
        if pat0_data is not None:
            material.add_pat0()
            self.__load_pat0(material.pat0, pat0_data)
        return material

    def __load_srt0(self, srt0, data):
        self.__load_settings(srt0, data.get('settings'))
        d = data.get('texture_animations')
        if d:
            if len(d) != len(srt0.tex_animations):
                raise self.MatToJsonError('srt0 texture animations do not have matching length, have {} enabled but {} '
                                          'found'.format(len(srt0.tex_animations), len(d)))
            for i in range(len(srt0.tex_animations)):
                self.__load_srt0_tex_anim(srt0.tex_animations[i], d[i])

    def __load_srt0_tex_anim(self, tex_anim, data):
        for x in data:
            self.__load_srt0_tex_anim_frame_list(tex_anim.animations[x], data[x])

    @staticmethod
    def __load_srt0_tex_anim_frame_list(frame_list, data):
        frame_list.entries = [
            SRTKeyFrameList.SRTKeyFrame(x['value'], x['frame'], x['delta'])
            for x in data
        ]

    def __load_pat0(self, pat0, data):
        self.__load_pat0_settings(pat0, data.get('settings'))
        frame_data = data.get('frames')
        self.__load_pat0_frames(pat0, frame_data)

    @staticmethod
    def __load_pat0_frames(pat0, data_frames):
        pat0.frames = [Pat0MatAnimation.Frame(x['frame'], x['texture'])
                       for x in data_frames]

    def __load_pat0_settings(self, pat0, data):
        if data:
            pat0.enabled = data['enabled']
            pat0.fixedTeture = data['fixed_texture']
            pat0.framecount = data['frame_count']
            pat0.loop = data['loop']

    def __load_layers(self, layers, data):
        i = 0
        for layer_name in data:
            layers[i].setName(layer_name)
            self.__load_settings(layers[i], data[layer_name])
            i += 1

    def __load_shader(self, shader, data):
        self.__load_settings(shader, data.get('settings'))
        i = 0
        stages_data = data.get('stages')
        if stages_data:
            for stage in stages_data:
                self.__load_settings(shader.stages[i], stages_data[stage])
                i += 1

    @staticmethod
    def __load_settings(item, settings):
        if settings:
            for x in settings:
                data = settings[x]
                if type(data) != str and type(data) != dict:
                    data = str(data)
                item.set_str(x, data)

    def __get_material_str(self, material):
        x = {'settings': self.__get_settings(material),
                'layers': self.__get_items_str(material.layers),
                'shader': self.__get_shader_str(material.shader)}
        if material.srt0 is not None:
            x['srt0'] = self.__get_srt0_str(material.srt0)
        if material.pat0 is not None:
            x['pat0'] = self.__get_pat0_str(material.pat0)
        return x

    def __get_shader_str(self, shader):
        return {'settings': self.__get_settings(shader),
                'stages': self.__get_items_str(shader.stages)}

    def __get_srt0_str(self, srt0):
        return {'settings': self.__get_settings(srt0),
                'texture_animations': [self.__get_srt0_tex_anim_str(x) for x in srt0.tex_animations]}

    def __get_srt0_tex_anim_str(self, tex_anim):
        r = {}
        for x in tex_anim.animations:
            r[x] = self.__get_srt0_tex_anim_frame_list(tex_anim.animations[x])
        return r

    def __get_srt0_tex_anim_frame_list(self, frame_list):
        return [
            {
                'frame': x.index,
                'value': x.value,
                'delta': x.delta
            }
            for x in frame_list.entries]

    def __get_pat0_str(self, pat0):
        return {
            'settings': self.__get_pat0_settings(pat0),
            'frames': self.__get_pat0_frames(pat0.frames)
        }

    def __get_pat0_frames(self, frames):
        return [{
            'frame': x.frame_id,
            'texture': x.tex
        } for x in frames]

    def __get_pat0_settings(self, pat0):
        return {
            'enabled': pat0.enabled,
            'fixed_texture': pat0.fixedTexture,
            'frame_count': pat0.framecount,
            'loop': pat0.loop,
        }

    def __get_items_str(self, items):
        ret = {}
        for x in items:
            ret[x.name] = self.__get_settings(x)
        return ret

    @staticmethod
    def __get_settings(item):
        settings = {}
        for setting in item.SETTINGS:
            settings[setting] = item.get_str(setting)
        return settings
