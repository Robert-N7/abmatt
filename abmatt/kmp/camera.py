from abmatt.kmp.base import Base


class Camera(Base):
    MAGIC = 'CAME'
    FMT = '4B3H2B15f'
    BYTE_LEN = 0x48

    def __init__(self, camera_type=0, next_camera=None, cam_shake=0, route=None,
                 point_speed=0, zoom_speed=0, view_speed=0, start=0, movie=0,
                 position=None, rotation=None, zoom_start=0, zoom_end=0,
                 view_start_pos=None, view_end_pos=None, time=0):
        self.time = time
        self.view_end_pos, self.view_start_pos, self.position, self.rotation = self.init_3((view_end_pos, view_start_pos,
                                                                                           position, rotation))
        self.zoom_end = zoom_end
        self.zoom_start = zoom_start
        self.movie = movie
        self.start = start
        self.view_speed = view_speed
        self.zoom_speed = zoom_speed
        self.point_speed = point_speed
        self.route = route
        self.cam_shake = cam_shake
        self.next_camera = next_camera
        self.camera_type = camera_type

    def __eq__(self, o):
        return self is o or super().__eq__(o) \
               and self.time == o.time and self.view_end_pos == o.view_end_pos \
               and self.view_start_pos == o.view_start_pos and self.position == o.position \
               and self.rotation == o.rotation and self.zoom_end == \
               o.zoom_end and self.zoom_start == o.zoom_start \
               and self.movie == o.movie and self.start == o.start and self.view_speed == o.view_speed \
               and self.zoom_speed == o.zoom_speed and self.point_speed == o.point_speed and self.route == o.route \
               and self.cam_shake == o.cam_shake \
               and self.camera_type == o.camera_type