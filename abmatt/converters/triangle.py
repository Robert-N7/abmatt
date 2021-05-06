from collections import deque
from struct import pack


def get_weighted_tri_groups(tri_strips, tris):
    # To encode the weighted triangles, we need to encode the matrices corresponding to the influences
    # These can only be a maximum of 10 at a time, so we may need to separate groups
    # Encode each group's matrices, tri_strips, and triangles
    groups = []
    group_matrices_sets = []
    group_tris = []
    for k in range(2):
        if k == 0:
            tri_list = tri_strips
            g = groups
            other_g = group_tris
        else:
            tri_list = tris
            g = group_tris
            other_g = groups
        for tri_strip in tri_list:
            new_infs = {x[0] for x in tri_strip}
            added = False
            best_group = -1
            best_group_add_count = 10
            for i in range(len(group_matrices_sets)):
                to_add = new_infs - group_matrices_sets[i]
                if len(to_add) <= 0:  # add
                    g[i].append(tri_strip)
                    added = True
                    break
                elif len(to_add) + len(group_matrices_sets[i]) <= 10 and len(to_add) < best_group_add_count:
                    best_group_add_count = len(to_add)
                    best_group = i
            if not added:
                if len(new_infs) > 10:
                    raise RuntimeError(
                        'Too many influences in tri-strip')  # Todo, split tristrip if it contains too many infs?
                if best_group >= 0:
                    g[best_group].append(tri_strip)
                    group_matrices_sets[best_group] |= new_infs
                else:
                    group_matrices_sets.append(new_infs)
                    g.append([tri_strip])
                    other_g.append([])
    group_matrices = [list(x) for x in group_matrices_sets]
    return groups, group_tris, group_matrices


def encode_triangle_strip(triangle_indices, fmt_str, byte_array):
    byte_array.extend(pack('>BH', 0x98, len(triangle_indices)))
    for x in triangle_indices:
        byte_array.extend(pack(fmt_str, *x))
    return len(triangle_indices)


def encode_triangles(triangle_indices, fmt_str, byte_array):
    face_point_len = len(triangle_indices) * 3
    byte_array.extend(pack('>BH', 0x90, face_point_len))
    for x in triangle_indices:
        for y in x:
            byte_array.extend(pack(fmt_str, *y))
    return face_point_len


class TriangleSet:
    triangles_in_strips_count = 0

    def __init__(self, np_tris):
        Triangle.edge_map = {}  # reset
        tris = []
        for tri in np_tris:
            verts = [tuple(x) for x in tri]
            tri_set = {x for x in verts}
            if len(tri_set) < 3:  # not a tri
                continue
            tris.append(Triangle(verts))
        self.triangles = tris

    def __bool__(self):
        return bool(self.triangles)

    def get_next(self, queue):
        while True:
            try:
                start = queue.pop(0)
            except IndexError:
                return None
            if not start.is_used:
                return start

    def get_tri_strips(self, fmt_str=None):
        queue = sorted(self.triangles, key=lambda tri: tri.get_connection_count())
        disconnected = []
        # weight_matrices = []        # maximum of 10 per group
        if fmt_str is None:
            tristrips = []
        else:
            tristrips = bytearray()
        face_point_count = 0
        # find the tri to start at
        while True:
            try:
                start = queue.pop(0)
            except IndexError:
                start = None
                break
            if start.connection_count > 0:
                break
            disconnected.append(start)
        # now try to generate strip
        while start is not None:
            strip = start.create_strip()
            if strip:
                if fmt_str:
                    face_point_count += encode_triangle_strip(strip, fmt_str, tristrips)
                else:
                    face_point_count += len(strip)
                    tristrips.append(strip)
                TriangleSet.triangles_in_strips_count += len(strip) - 2
            else:
                disconnected.append(start)
            start = self.get_next(queue)
        if len(disconnected):
            if fmt_str:
                face_point_count += encode_triangles(disconnected, fmt_str, tristrips)
            else:
                face_point_count += len(disconnected) * 3
        # print('Total tristrip triangles {}'.format(self.triangles_in_strips_count))
        return tristrips, len(self.triangles), face_point_count, disconnected

    # def __create_strip_weights(self, strip, weight_matrices):
    #     unadded_weight_indices = {vertex[0] for vertex in strip if vertex[0] not in weight_matrices}
    #     if len(unadded_weight_indices) + len(weight_matrices) >



class Triangle:
    edge_map = {}

    class Edge:
        def __str__(self):
            return str(self.verts)

        def __init__(self, tri, edge):
            self.tris = [tri]
            self.verts = edge

        def __bool__(self):
            return bool(self.tris)

        def tri_count(self):
            return len(self.tris)

        def disconnect(self, tri):
            self.tris.remove(tri)

        def reconnect(self, tri):
            self.tris.append(tri)

        def get_adjacent(self, current):
            for x in self.tris:
                if x != current and not x.is_used:
                    return x

    def get_edge(self, edge):
        c_edge = self.edge_map.get(edge)
        if c_edge is None:
            c_edge = self.Edge(self, edge)
            self.edge_map[edge] = c_edge
            self.edge_map[(edge[1], edge[0])] = c_edge
        else:
            c_edge.tris.append(self)
        return c_edge

    def __iter__(self):
        return iter(self.vertices)

    def __next__(self):
        return next(self.vertices)

    def __init__(self, vertices):
        self.vertices = vertices
        self.is_used = False  # is it in a tri strip?
        self.edges = [self.get_edge((vertices[0], vertices[1])),
                      self.get_edge((vertices[1], vertices[2])),
                      self.get_edge((vertices[2], vertices[0]))]

    def __str__(self):
        return str(self.vertices)

    def get_opposite_vert(self, edge):
        i = self.edges.index(edge)
        return self.vertices[i - 1]

    def get_next_edge(self, edge):
        startI = self.nextI(self.edges.index(edge))
        return self.vertices[startI], self.vertices[self.nextI(startI)]

    def get_prev_edge(self, edge):
        i = self.edges.index(edge)
        return self.vertices[i - 1], self.vertices[i]

    def get_connection_count(self):
        count = 0
        edges = self.edges
        for i in range(3):
            count += edges[i].tri_count() - 1  # ignore self
        self.connection_count = count
        return count

    def disconnect(self):
        self.is_used = True
        for x in self.edges:
            x.disconnect(self)

    def reconnect(self):
        self.is_used = False
        for x in self.edges:
            x.reconnect(self)

    @staticmethod
    def nextI(currentI):
        return currentI + 1 if currentI < 2 else 0

    def create_strip(self):
        # self.disconnect()  # disconnect
        edges = self.edges
        for i in range(3):
            edge = edges[i]
            if edge.tri_count() > 1:
                self.disconnect()
                vertices = self.vertices
                adjacent = edge.get_adjacent(self)
                adjacent.disconnect()
                right_vert = adjacent.get_opposite_vert(edge)
                vert_strip = deque((vertices[i - 1], vertices[i], vertices[self.nextI(i)], right_vert))
                return adjacent.extend_right(vert_strip, (vert_strip[2], vert_strip[3]))
                # return self.extend_left(vert_strip, (vert_strip[0], vert_strip[1]))
                # return vert_strip

    def extend_right(self, strip, last_verts):
        edge = self.edge_map[last_verts]
        if not edge.tri_count():
            return strip
        adj = edge.get_adjacent(self)
        adj.disconnect()
        vert = adj.get_opposite_vert(edge)
        strip.append(vert)
        return adj.extend_right(strip, (last_verts[1], vert))

    def extend_left(self, strip, last_verts, cull_wrong=False):
        edge = self.edge_map[last_verts]
        if not edge.tri_count():
            if cull_wrong:
                self.reconnect()
                strip.popleft()
            return strip
        adj = edge.get_adjacent(self)
        adj.disconnect()
        vert = adj.get_opposite_vert(edge)
        strip.appendleft(vert)
        return adj.extend_left(strip, (vert, last_verts[0]), not cull_wrong)
