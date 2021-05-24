from abmatt.brres.lib.node import Node


class Light(Node):
    def begin(self):
        self.node_id = 0
        self.real_id = 0
        self.non_spec_light_id = 0
        self.fixed_flags = 0
        self.usage_flags = 0
        self.vis_offset = 0
        self.start_point = [0.0, 0.0, 0.0]
        self.light_color = [0, 0, 0, 0]
        self.end_point = [0.0, 0.0, 0.0]
        self.dist_func = 0
        self.ref_distance = 0.0
        self.ref_brightness = 0.0
        self.spot_func = 0
        self.cutoff = 0.0
        self.specular_color = 0
        self.shinyness = 0.0

    def __eq__(self, other):
        return super().__eq__(other) and self.node_id == other.node_id \
               and self.real_id == other.real_id and self.non_spec_light_id == other.non_spec_light_id \
               and self.fixed_flags == other.fixed_flags and self.usage_flags == other.usage_flags \
               and self.vis_offset == other.vis_offset and self.start_point == other.start_point \
               and self.end_point == other.end_point and self.light_color == other.light_color \
               and self.dist_func == other.dist_func and self.ref_distance == other.ref_distance \
               and self.ref_brightness == other.ref_brightness and self.spot_func == other.spot_func \
               and self.cutoff == other.cutoff and self.specular_color == other.specular_color \
               and self.shinyness == other.shinyness


class AmbientLight(Node):
    def begin(self):
        self.node_id = 0
        self.real_id = 0
        self.fixed_flags = 0
        self.flags = 0
        self.lighting = [0, 0, 0, 0]

    def __eq__(self, other):
        return super().__eq__(other) and self.node_id == other.node_id and self.real_id == other.real_id \
               and self.fixed_flags == other.fixed_flags and self.flags == other.flags \
               and self.lighting == other.lighting

class LightSet(Node):
    def begin(self):
        self.node_id = 0
        self.real_id = 0
        self.ambient_name = ''
        self.light_names = []

    def __eq__(self, other):
        return super().__eq__(other) and self.node_id == other.node_id and self.real_id == other.real_id \
               and self.ambient_name == other.ambient_name and self.light_names == other.light_names
