from abmatt.lib.node import Node


class Camera(Node):
    def begin(self):
        self.node_id = 0
        self.real_id = 0
        self.projection_type = 0
        self.flags1 = 0
        self.flags2 = 0
        self.position = [0.0, 0.0, 0.0]
        self.aspect = 0.0
        self.near_z = 0.0
        self.far_z = 0.0
        self.rotate = [0.0, 0.0, 0.0]
        self.aim = [0.00, 0.0, 0.0]
        self.twist = 0.0
        self.persp_fov_y = 0.0
        self.ortho_height = 0.0

    def __eq__(self, other):
        return super().__eq__(other) and self.node_id == other.node_id and self.real_id == other.real_id \
               and self.projection_type == other.projection_type and self.flags1 == other.flags1 \
               and self.flags2 == other.flags2 and self.position == other.position and self.aspect == other.aspect \
               and self.near_z == other.near_z and self.far_z == other.far_z and self.rotate == other.rotate \
               and self.aim == other.aim and self.twist == other.twist and self.persp_fov_y == other.persp_fov_y \
               and self.ortho_height == other.ortho_height