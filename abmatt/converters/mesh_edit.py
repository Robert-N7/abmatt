import math

import numpy as np

from abmatt.converters.matrix import euler_to_rotation_matrix, IDENTITY, scale_matrix


class MeshPoint:
    def __init__(self, p_group, index):
        self.p_group = p_group
        self.index = index

    def set(self, value):
        self.p_group.data[self.index] = value

    def get(self):
        return self.p_group.data[self.index]

    def dist(self, point):
        p1 = np.array(self.get())
        p2 = np.array(point.get())
        return np.sqrt(np.sum((p1 - p2)**2, axis=0))

    def __str__(self):
        return str(self.p_group.data[self.index])


class MeshEdit:
    def __init__(self, mdl0):
        self.mdl0 = mdl0

    @staticmethod
    def in_box(point, bound1, bound2):
        for i in range(len(bound1)):
            if bound1[i] < bound2[i]:
                if not bound1[i] <= point[i] <= bound2[i]:
                    return False
            else:
                if not bound2[i] <= point[i] <= bound1[i]:
                    return False
        return True

    def select_verts(self, point1=(-math.inf, -math.inf, -math.inf),
                     point2=(math.inf, math.inf, math.inf),
                     polygons=None):
        if not polygons:
            polygons = self.mdl0.objects
        elif type(polygons[0]) is str:
            polygons = [x for x in self.mdl0.objects if x.name in polygons]
        ret = []
        for x in polygons:
            vertices = x.get_vertex_group()
            for i in range(len(vertices)):
                if self.in_box(vertices.data[i], point1, point2):
                    ret.append(MeshPoint(vertices, i))
        return ret

    def shift(self, mesh_points, shift):
        for x in mesh_points:
            x.set(np.array(x.get()) + shift)

    def get_clusters(self, mesh_points, dist=3000):
        clusters = []
        for p in mesh_points:
            added = False
            for c in clusters:
                if type(dist) is not list and type(dist) is not tuple:
                    if p.dist(c[0]) < dist:
                        c.append(p)
                        added = True
                        break
                else:
                    within = True
                    for i in range(3):
                        x = p.get()
                        y = c[0].get()
                        if abs(y[i] - x[i]) > dist[i]:
                            within = False
                            break
                    if within:
                        c.append(p)
                        added = True
                        break
            if not added:
                clusters.append([p])
        return clusters

    def rotate_all_uvs(self, mesh_points, range=3000):
        for c in self.get_clusters(mesh_points, range):
            self.rotate_uv(c)

    def rotate_uv(self, box_points):
        rotation = len(box_points) // 2
        original = [x.get() for x in box_points]
        for i in range(len(box_points)):
            box_points[i].set(original[(i + rotation) % len(box_points)])

    def rotate_all(self, mesh_points, rotation=(0, 180, 0), range=3000, box_point=None):
        point_of_origin = None
        for c in self.get_clusters(mesh_points, range):
            if box_point:
                point_of_origin = self.get_box_point(c, box_point)
            self.rotate(c, rotation, point_of_origin)

    def rotate(self, mesh_points, euler_angles=(0, 180, 0), point_of_origin=None):
        # todo normals
        self.transform_about(point_of_origin, mesh_points,
                             lambda x: np.matmul(x, euler_to_rotation_matrix(euler_angles)))

    def transform_about(self, point_of_origin, mesh_points, transform_func):
        if point_of_origin is None:
            point_of_origin = self.get_box_point(mesh_points, (0.5, 0, 0.5))
        points = np.array([x.get() for x in mesh_points])
        points -= point_of_origin
        points = transform_func(points)
        points += point_of_origin
        for i in range(len(points)):
            mesh_points[i].set(points[i])

    def scale(self, mesh_points, scale, point_of_origin=None):
        self.transform_about(point_of_origin, mesh_points,
                             lambda x: np.matmul(x, scale_matrix(IDENTITY, scale)[:3, :3]))

    def get_box(self, mesh_points):
        base = [x for x in mesh_points[0].get()]
        top = [x for x in base]
        width = len(top)
        for p in mesh_points:
            v = p.get()
            for i in range(width):
                if v[i] < base[i]:
                    base[i] = v[i]
                if v[i] > top[i]:
                    top[i] = v[i]
        return np.array(base), np.array(top)

    def get_box_point(self, mesh_points, box_loc):
        """
        Get the box point on mesh using box location
        :param mesh_points: Mesh
        :param box_loc: ndarray [x, y, z] location on box ranging from 0, 1 where 1 is the uppermost on box
        """
        base, top = self.get_box(mesh_points)
        return base + (top - base) * box_loc
