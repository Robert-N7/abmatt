import struct

from abmatt.kmp.area import Area
from abmatt.kmp.camera import Camera
from abmatt.kmp.cannon import Cannon
from abmatt.kmp.checkpoint import CheckPoint
from abmatt.kmp.cpu_route import CpuRoutePoint
from abmatt.kmp.end_position import EndPosition
from abmatt.kmp.game_object import GameObject
from abmatt.kmp.item_route import ItemRoutePoint
from abmatt.kmp.lib.packing.pack_section import PackEnph, PackItph, PackCkph, PackSection
from abmatt.kmp.respawn import Respawn
from abmatt.kmp.route import Route, RoutePoint
from abmatt.kmp.stage_info import StageInfo
from abmatt.kmp.start_position import StartPosition
from abmatt.lib.indexing import rebuild_indexes, get_id
from abmatt.lib.pack_interface import Packer


class PackArea(PackSection):
    klass = Area

    def pack_data(self, area, binfile):
        binfile.write(self.klass.FMT, area.shape, area.area_type,
                      get_id(area.camera), area.priority,
                      *area.position, *area.rotation, *area.scale, *area.settings,
                      get_id(area.route), area.enemy_point_id, 0)


class PackCame(PackSection):
    klass = Camera

    def pack_data(self, cam, binfile):
        binfile.write(self.klass.FMT, cam.camera_type,
                      get_id(cam.next_camera),
                      cam.cam_shake,
                      get_id(cam.route), cam.point_speed, cam.zoom_speed,
                      cam.view_speed, cam.start, cam.movie,
                      *cam.position, *cam.rotation, cam.zoom_start, cam.zoom_end,
                      *cam.view_start_pos, *cam.view_end_pos, cam.time)


class PackCkpt(PackSection):
    klass = CheckPoint

    def pack_data(self, checkpoint, binfile):
        binfile.write(self.klass.FMT, *checkpoint.left_pole, *checkpoint.right_pole,
                      get_id(checkpoint.respawn),
                      checkpoint.key, get_id(checkpoint.previous), get_id(checkpoint.next))


class PackCnpt(PackSection):
    klass = Cannon

    def pack_data(self, cannon, binfile):
        binfile.write(self.klass.FMT, *cannon.position, *cannon.rotation, cannon.index, cannon.shoot_effect)


class PackEnpt(PackSection):
    klass = CpuRoutePoint

    def pack_data(self, point, binfile):
        binfile.write(self.klass.FMT, *point.position, point.width, *point.settings)


class PackGobj(PackSection):
    klass = GameObject

    def pack_data(self, object, binfile):
        binfile.write(self.klass.FMT, object.id, object.extended_presence, *object.position,
                      *object.rotation, *object.scale, get_id(object.route, 0xffff),
                      *object.settings, object.presence)


class PackItpt(PackSection):
    klass = ItemRoutePoint

    def pack_data(self, point, binfile):
        binfile.write(self.klass.FMT, *point.position, point.width, *point.settings)


class PackJgpt(PackSection):
    klass = Respawn

    def pack_data(self, node, binfile):
        binfile.write(self.klass.FMT, *node.position, *node.rotation, node.index, node.range)


class PackKtpt(PackSection):
    klass = StartPosition

    def pack_data(self, node, binfile):
        binfile.write(self.klass.FMT, *node.position, *node.rotation, node.player_id, 0)


class PackMspt(PackSection):
    klass = EndPosition

    def pack_data(self, node, binfile):
        binfile.write(self.klass.FMT, *node.position, *node.rotation, node.index, node.unknown)


class PackPoti(PackSection):
    klass = Route

    def get_added_value(self):
        return sum([len(x) for x in self.node])

    def pack_data(self, route, binfile):
        binfile.write(self.klass.FMT, len(route), *route.settings)
        for point in route:
            binfile.write(RoutePoint.FMT, *point.position, point.speed, point.setting)


class PackStgi(PackSection):
    klass = StageInfo

    def pack_data(self, node, binfile):
        b = struct.pack('f', node.speed_mod)
        binfile.write(self.klass.FMT, node.lap_count, node.pole_position_right, node.narrow, node.lens_flashing,
                      0, *node.flare_color, 0, b[0], b[1])

       
class PackKmp(Packer):
    packers = [PackKtpt, PackEnpt, PackEnph, PackItpt, PackItph, PackCkpt, PackCkph,
               PackGobj, PackPoti, PackArea, PackCame, PackJgpt, PackCnpt, PackMspt,
               PackStgi]

    @staticmethod
    def build_point_group(groups_collection):
        return [[x for group in groups for x in group]
                for groups in groups_collection]

    def pre_packing(self, kmp):
        enpt, itpt, ckpt = self.build_point_group((kmp.cpu_routes, kmp.item_routes, kmp.check_points))
        sections = [kmp.start_positions, enpt, kmp.cpu_routes, itpt, kmp.item_routes,
                ckpt, kmp.check_points, kmp.game_objects, kmp.routes, kmp.areas, kmp.cameras,
                kmp.respawns, kmp.cannons, kmp.end_positions, kmp.stage_info]
        for x in sections:
            rebuild_indexes(x)
        # update came opening cam values
        kmp.additional_values[10] = get_id(kmp.pan_cam, 0xff) << 8 | get_id(kmp.movie_cam, 0xff)
        return sections

    def pack(self, kmp, binfile):
        sections = self.pre_packing(kmp)
        offset = binfile.start()
        binfile.write_magic(kmp.MAGIC)
        binfile.mark_len()
        binfile.write('2HI', 15, 0x4c, kmp.version)
        binfile.mark(15)
        binfile.beginOffset = len(binfile.file)     # offsets from header end
        for i in range(15):
            binfile.create_ref()
            self.packers[i](sections[i], binfile, kmp.additional_values[i])
        binfile.beginOffset = offset
        binfile.end()


