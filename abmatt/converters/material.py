import os

from abmatt.brres.mdl0.material import material


class Material:
    def __init__(self, name, diffuse_map=None, ambient_map=None, specular_map=None, transparency=0):
        self.name = name
        self.ambient_map = ambient_map
        self.diffuse_map = diffuse_map
        self.specular_map = specular_map
        self.transparency = transparency

    def get_maps(self):
        maps = set()
        maps.add(self.ambient_map)
        maps.add(self.diffuse_map)
        maps.add(self.specular_map)
        if None in maps:
            maps.remove(None)
        return maps

    @staticmethod
    def encode_map(map, material, used_layers):
        if map:
            layer_name = os.path.splitext(os.path.basename(map))[0]
            if layer_name not in used_layers:
                material.add_layer(layer_name)
                used_layers.add(layer_name)

    def encode(self, mdl):
        m = material.Material.get_unique_material(self.name, mdl)
        mdl.add_material(m)
        if self.transparency > 0:
            m.enable_blend()
        # maps
        layers = set()
        self.encode_map(self.diffuse_map, m, layers)
        self.encode_map(self.ambient_map, m, layers)
        self.encode_map(self.specular_map, m, layers)
        return m


def decode_material(mdl0_mat):
    m = Material(mdl0_mat.name)
    if mdl0_mat.xlu:
        m.transparency = 0.5
    layers = mdl0_mat.layers
    for i in range(len(layers)):
        if i == 0:
            m.diffuse_map = layers[i].name
        elif i == 1:
            m.ambient_map = layers[i].name
        elif i == 2:
            m.specular_map = layers[i].name
    return m

