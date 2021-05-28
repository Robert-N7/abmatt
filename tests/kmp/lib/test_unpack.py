import numpy as np

from tests.kmp.lib.test_kmp_lib import KmpTest


class TestUnpack(KmpTest):
    def _test_beginner(self, kmp):
        self.kmp = kmp
        self.assertEqual(1, len(kmp.start_positions))
        self.assertEqual(6, len(kmp.cpu_routes))
        self.assertEqual(0x16, len(kmp.item_routes))
        self.assertEqual(1, len(kmp.check_points))
        self.assertEqual(0x10, len(kmp.routes))
        self.assertEqual(9, len(kmp.areas))
        self.assertEqual(0x10, len(kmp.cameras))
        self.assertEqual(1, len(kmp.respawns))
        self.assertEqual(1, len(kmp.cannons))
        self.assertEqual(1, len(kmp.end_positions))
        self.assertEqual(1, len(kmp.stage_info))
        self.__test_start_position(kmp.start_positions[0])
        self.__test_enpt(kmp.cpu_routes[0])
        self.__test_itpt(kmp.item_routes[0])
        self.__test_ckpt(kmp.check_points[0])
        self.__test_area(kmp.areas[0])
        self.__test_came(kmp.cameras[0])
        self.__test_respawn(kmp.respawns[0])
        self.__test_stgi(kmp.stage_info[0])
        self.__test_cannon(kmp.cannons[0])
        self.__test_mspt(kmp.end_positions[0])

    def test_unpack(self):
        self._test_beginner(self._get_kmp('beginner.kmp'))

    def __test_start_position(self, start):
        self.assertTrue(np.allclose([-20115, 470.3823, 25750], start.position))
        self.assertEqual([0, 180, 0], start.rotation)
        self.assertEqual(0xffff, start.player_id)

    def __test_prev_next(self, item, objects, expected_prev, expected_next):
        self.assertEqual(expected_next,
                         [objects.index(x) for x in item.next_groups])
        self.assertEqual(expected_prev,
                         [objects.index(x) for x in item.prev_groups])

    def __test_enpt(self, enpt):
        self.__test_prev_next(enpt, self.kmp.cpu_routes, [1], [4, 5])
        self.assertEqual(0x11, len(enpt.points))
        item = enpt[0]
        self.assertTrue(np.allclose([-20100, 512.6353, 22000], item.position))
        self.assertEqual(25, item.width)
        self.assertEqual([3, 0, 0], item.settings)

    def __test_itpt(self, itpt):
        self.__test_prev_next(itpt, self.kmp.item_routes, [3, 7], [1, 4])
        self.assertEqual(0x3, len(itpt))
        item = itpt[0]
        self.assertTrue(np.allclose([-19950, 529.0695, 21306.1], item.position))
        self.assertEqual(40, item.width)
        self.assertEqual([0, 0], item.settings)

    def __test_ckpt(self, ckpt):
        self.__test_prev_next(ckpt, self.kmp.check_points, [0], [0])
        self.assertEqual(0x17, len(ckpt))
        item = ckpt[0]
        self.assertTrue(np.allclose([-25500, 25600], item.left_pole))
        self.assertTrue(np.allclose([-16350, 25600], item.right_pole))
        self.assertIsNotNone(item.respawn)
        self.assertEqual(0, item.key)
        self.assertEqual(1, item.next.key)
        self.assertIsNone(item.previous)

    def __test_poti(self, poti):
        self.assertEqual(2, len(poti))
        item = poti[0]
        self.assertTrue(
            np.allclose([-19202.67, 642.5624, 19820.77], item.position))
        self.assertEqual([0x3c, 0], item.settings)

    def __test_area(self, area):
        self.assertEqual(0, area.area_type)
        self.assertEqual(0, area.shape)
        self.assertIsNone(area.route)
        self.assertIsNotNone(area.camera)
        self.assertTrue(np.allclose([1, 1, 1.75], area.scale))
        self.assertTrue(np.allclose([0, 0, 0], area.rotation))
        self.assertTrue(
            np.allclose([-20593.49, -166.3846, 29108.6], area.position))
        self.assertEqual([0, 0], area.settings)
        self.assertEqual(0xff, area.enemy_point_id)

    def __test_came(self, cam):
        self.assertEqual(0, cam.camera_type)
        self.assertIsNone(cam.next_camera)
        self.assertEqual(0, cam.cam_shake)
        self.assertIsNone(cam.route)
        self.assertEqual(0, cam.point_speed)
        self.assertEqual(0x1e, cam.zoom_speed)
        self.assertEqual(0, cam.view_speed)
        self.assertEqual(0, cam.start)
        self.assertEqual(0, cam.movie)
        self.assertTrue(
            np.allclose([-26663.19, 6073.401, 25696.73], cam.position))
        self.assertEqual(85, cam.zoom_start)
        self.assertEqual(40, cam.zoom_end)
        self.assertEqual(0, cam.time)
        self.assertTrue(np.allclose([-30, -1, 550], cam.view_start_pos))
        self.assertTrue(np.allclose([-5, 1, 0], cam.view_end_pos))

    def __test_respawn(self, respawn):
        self.assertTrue(
            np.allclose([-20115, 472.9309, 26750], respawn.position))
        self.assertTrue(np.allclose([0, 180, 0], respawn.rotation))
        self.assertEqual(0xffff, respawn.range)

    def __test_stgi(self, stgi):
        self.assertEqual(3, stgi.lap_count)
        self.assertTrue(stgi.pole_position_right)
        self.assertFalse(stgi.narrow)
        self.assertTrue(stgi.lens_flashing)
        self.assertEqual([0xff, 0xff, 0xff, 0x4b], stgi.flare_color)
        self.assertEqual(0, stgi.speed_mod)

    def __test_cannon(self, cannon):
        self.assertTrue(np.allclose([1222, 333, 322], cannon.position))
        self.assertTrue(np.allclose([1, 5, 8], cannon.rotation))
        self.assertEqual(1, cannon.shoot_effect)

    def __test_mspt(self, end_pos):
        self.assertTrue(np.allclose([1, 2, 3], end_pos.position))
        self.assertTrue(np.allclose([4, 5, 6], end_pos.rotation))
        self.assertEqual(6, end_pos.unknown)
