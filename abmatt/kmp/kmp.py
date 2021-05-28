import os

from abmatt.autofix import AutoFix
from abmatt.kmp.lib.packing.pack_kmp import PackKmp
from abmatt.kmp.lib.unpacking.unpack_kmp import UnpackKmp
from abmatt.kmp.respawn import Respawn
from abmatt.kmp.stage_info import StageInfo
from abmatt.kmp.start_position import StartPosition
from abmatt.lib.binfile import BinFile
from abmatt.lib.node import Packable


class Kmp(Packable):
    MAGIC = 'RKMD'

    @property
    def is_battle_mode(self):
        return len(self.end_positions) > 0

    def __init__(self, name, parent=None, read_file=True):
        name = os.path.abspath(name)
        binfile = BinFile(name) if read_file else None
        super().__init__(name, parent, binfile)
        if binfile:
            self.unpack(binfile)

    def get_height_at(self, x=0, z=0):
        return 10000

    def begin(self):
        self.version = 0x9d8
        self.stage_info = [StageInfo()]
        self.areas = []
        self.cameras = []
        self.check_points = []
        self.cannons = []
        self.cpu_routes = []
        self.game_objects = []
        self.item_routes = []
        self.respawns = []
        self.start_positions = [StartPosition()]
        self.end_positions = []
        self.routes = []
        self.pan_cam = None
        self.movie_cam = None
        self.additional_values = [0] * 15

    def unpack(self, binfile):
        UnpackKmp(self, binfile)

    def pack(self, binfile):
        PackKmp(self, binfile)

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.version == other.version and \
            self.stage_info == other.stage_info and \
            self.areas == other.areas and \
            self.cameras == other.cameras and \
            self.check_points == other.check_points and \
            self.cannons == other.cannons and \
            self.cpu_routes == other.cpu_routes and \
            self.game_objects == other.game_objects and \
            self.item_routes == other.item_routes and \
            self.respawns == other.respawns and \
            self.start_positions == other.start_positions and \
            self.end_positions == other.end_positions and \
            self.routes == other.routes and \
            self.pan_cam == other.pan_cam and \
            self.movie_cam == other.movie_cam

    def check(self):
        if not self.respawns:
            AutoFix.warn('No respawns found! Adding generic...')
            self.respawns.append(Respawn([0, self.get_height_at(), 0]))

        # todo add cams
        if not self.pan_cam:
            AutoFix.warn('No opening pan camera!')
        if not self.movie_cam:
            AutoFix.warn('No movie cam!')

