import sys

from abmatt.kmp.base import ConnectedPointCollection
from abmatt.kmp.checkpoint import CheckPoint
from abmatt.kmp.kmp import Kmp


def reverse_kmp(kmp):
    """Reverses kmp (EXPERIMENTAL, this only gives a starting place)"""
    if type(kmp) == str:
        kmp = Kmp(kmp)
    for route in [kmp.routes, kmp.check_points, kmp.item_routes, kmp.cpu_routes]:
        reverse_route(route)
    reorder_key_checkpoints(kmp.check_points)
    rotate_group(kmp.respawns)
    rotate_group(kmp.start_positions)
    return kmp


def rotate_group(group):
    for item in group:
        item.rotation = item.rotation + 180 % 360


def reorder_key_checkpoints(checkpoints):
    key_points = {}  # create map to key checkpoints
    for group in checkpoints:
        for x in group:
            if x.key != 0xff:
                if x.key in key_points:
                    raise ValueError(f'Duplicate checkpoint key {x.key}')
                key_points[x.key] = x

    key_sorted = sorted(list(key_points.keys()), reverse=True)
    for i in range(len(key_sorted)):
        key_points[key_sorted[i]].key = i + 1
    key_points[-1].key = 0


def reverse_route(route):
    route.points.reverse()
    if issubclass(route, ConnectedPointCollection):
        t = route.prev_groups
        route.prev_groups = route.next_groups
        route.next_groups = t
        if type(route) is CheckPoint:
            for check in route:
                t = check.next
                check.next = check.previous
                check.previous = t
                t = check.left_pole
                check.left_pole = check.right_pole
                check.right_pole = t


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: reverse <kmp_file> <destination>')
        sys.exit(-1)
    reversed = reverse_kmp(Kmp(sys.argv[1]))
    reversed.save(sys.argv[2])
