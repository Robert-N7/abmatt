import struct

from abmatt.kmp.area import Area
from abmatt.kmp.camera import Camera
from abmatt.kmp.cannon import Cannon
from abmatt.kmp.checkpoint import CheckPointGroup, CheckPoint
from abmatt.kmp.cpu_route import CpuRoute, CpuRoutePoint
from abmatt.kmp.end_position import EndPosition
from abmatt.kmp.game_object import GameObject
from abmatt.kmp.item_route import ItemRoute, ItemRoutePoint
from abmatt.kmp.lib.unpacking.unpack_section import UnpackSection, UnpackHead
from abmatt.kmp.respawn import Respawn
from abmatt.kmp.route import Route, RoutePoint
from abmatt.kmp.stage_info import StageInfo
from abmatt.kmp.start_position import StartPosition
from abmatt.lib.binfile import UnpackingError
from abmatt.lib.unpack_interface import Unpacker


class UnpackCame(UnpackSection):
    klass = Camera

    def post_unpack(self, args):
        routes = self.node.routes
        for cam in self.nodes:
            cam.next_camera = self.resolve(self.nodes, cam.next_camera)
            cam.route = self.resolve(routes, cam.route)
        self.node.cameras = self.nodes
        pan_cam = self.additional_val >> 8 & 0xff
        movie_cam = self.additional_val & 0xff
        self.node.pan_cam = self.resolve(self.nodes, pan_cam)
        self.node.movie_cam = self.resolve(self.nodes, movie_cam)

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return Camera(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8],
                      x[9:12], x[12:15], x[15], x[16], x[17:20], x[20:23], x[23])


class UnpackArea(UnpackSection):
    klass = Area

    def post_unpack(self, args):
        areas = []
        for n in self.nodes:
            areas.append(Area(n[0], n[1], self.resolve(self.node.cameras, n[2]),
                              priority=n[3], position=n[4:7], rotation=n[7:10], scale=n[10:13],
                              settings=[n[13], n[14]], route=self.resolve(self.node.routes, n[15]), enemy_point_id=n[16]))
        self.node.areas = areas


class UnpackCkph(UnpackHead):
    klass = CheckPointGroup

    def post_unpack(self, args):
        self.node.check_points = super().post_unpack(args)


class UnpackCkpt(UnpackSection):
    klass = CheckPoint

    def post_unpack(self, args):
        respawns = self.node.respawns
        for n in self.nodes:
            n.previous = self.resolve(self.nodes, n.previous)
            n.next = self.resolve(self.nodes, n.next)
            n.respawn = self.resolve(respawns, n.respawn)
        return self.nodes

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return CheckPoint(x[0:2], x[2:4], x[4], x[5], x[6], x[7])


class UnpackCnpt(UnpackSection):
    klass = Cannon

    def post_unpack(self, args):
        self.node.cannons = [Cannon(x[0:3], x[3:6], x[7]) for x in self.nodes]


class UnpackEnph(UnpackHead):
    klass = CpuRoute

    def post_unpack(self, args):
        route_groups = super().post_unpack(args)
        for i in range(len(route_groups)):
            x = self.nodes[i]
            route_groups[i].dispatch_points = [x[14], x[15]]
        self.node.cpu_routes = route_groups


class UnpackEnpt(UnpackSection):
    klass = CpuRoutePoint

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return CpuRoutePoint(x[0:3], x[3], [x[4], x[5], x[6]])


class UnpackGobj(UnpackSection):
    klass = GameObject

    def post_unpack(self, args):
        routes = self.node.routes
        for n in self.nodes:
            n.route = self.resolve(routes, n.route)
        self.node.game_objects = self.nodes

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return GameObject(x[0], x[1], x[2:5], x[5:8], x[8:11], x[11], x[12:20], x[20])


class UnpackItph(UnpackHead):
    klass = ItemRoute

    def post_unpack(self, args):
        self.node.item_routes = super().post_unpack(args)


class UnpackItpt(UnpackSection):
    klass = ItemRoutePoint

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return ItemRoutePoint(x[0:3], x[3], x[4:])


class UnpackJgpt(UnpackSection):
    klass = Respawn

    def post_unpack(self, args):
        self.node.respawns = self.nodes

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return Respawn(x[0:3], x[3:6], x[7])


class UnpackKtpt(UnpackSection):
    klass = StartPosition

    def post_unpack(self, args):
        self.node.start_positions = self.nodes

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return StartPosition(x[0:3], x[3:6], x[6])


class UnpackMspt(UnpackSection):
    klass = EndPosition

    def post_unpack(self, args):
        self.node.end_positions = [EndPosition(x[0:3], x[3:6], x[7]) for x in self.nodes]


class UnpackPoti(UnpackSection):
    klass = Route

    def post_unpack(self, args):
        self.node.routes = self.nodes

    def unpack_data(self, binfile):
        n, s1, s2 = super().unpack_data(binfile)
        p = []
        for i in range(n):
            x = binfile.read(RoutePoint.FMT, RoutePoint.BYTE_LEN)
            p.append(RoutePoint(x[0:3], x[3], x[4]))
        return Route(p, [s1, s2])


class UnpackStgi(UnpackSection):
    klass = StageInfo

    def post_unpack(self, args):
        self.node.stage_info = self.nodes

    def unpack_data(self, binfile):
        x = super().unpack_data(binfile)
        return StageInfo(x[0], x[1], x[2], x[3], list(x[5:9]), struct.unpack('f', bytes((x[10], x[11], 0, 0)))[0])


class UnpackKmp(Unpacker):
    unpackers = [UnpackKtpt, UnpackEnpt, UnpackEnph, UnpackItpt, UnpackItph, UnpackCkpt, UnpackCkph,
                 UnpackGobj, UnpackPoti, UnpackArea, UnpackCame, UnpackJgpt, UnpackCnpt, UnpackMspt, UnpackStgi]

    def unpack(self, node, binfile):
        start = binfile.start()
        if binfile.read_magic() != node.MAGIC:
            raise UnpackingError(binfile, 'Not a kmp file!')
        binfile.read_len()
        n_sections, head_length, node.version = binfile.read('2HI', 8)
        if node.version != 0x9d8:
            raise UnpackingError(binfile, 'Unsupported kmp version {}'.format(node.version))
        current = binfile.offset
        binfile.offset = start + head_length
        binfile.start()  # Reference from the end of the header
        binfile.offset = current
        binfile.store(n_sections)
        u = []
        additional_values = []
        for i in range(n_sections):
            binfile.recall()
            unpacker = self.unpackers[i](node, binfile)
            u.append(unpacker)
            additional_values.append(unpacker.additional_val)
        binfile.end()
        binfile.end()

        # post-unpack
        # routes, respawns, cameras, and the rest can fall in normal order
        node.additional_values = additional_values
        post_unpack_order = [8, 10, 11]
        post_unpack_order.extend([x for x in range(15) if x not in post_unpack_order])
        for i in post_unpack_order:
            prev = u[i - 1].nodes if i > 0 else None
            u[i].post_unpack(prev)
