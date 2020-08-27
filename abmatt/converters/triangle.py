from collections import deque
from struct import pack


def encode_triangle_strip(triangle_indices, fmt_str, byte_array):
    byte_array.extend(pack('>BH', 0x98, len(triangle_indices)))
    for x in triangle_indices:
        byte_array.extend(pack(fmt_str, *x))
    return len(triangle_indices)


def encode_triangles(triangle_indices, fmt_str, byte_array):
    face_point_len = len(triangle_indices) * 3
    byte_array.extend(pack('>BH', 0x90, face_point_len))
    for x in triangle_indices:
        for y in x.vertices:
            byte_array.extend(pack(fmt_str, *y))
    return face_point_len


class TriangleSet:
    triangles_in_strips_count = 0

    def __init__(self, np_tris):
        Triangle.edge_map = {}  # reset
        tris = []
        total_set = {}
        for tri in np_tris:
            verts = [tuple(x) for x in tri]
            tri_set = {x for x in verts}
            if len(tri_set) < 3:  # not a tri
                continue
            tris.append(Triangle(verts))
        self.triangles = tris

    def get_tri_strips(self, fmt_str):
        queue = sorted(self.triangles, key=lambda tri: tri.get_connection_count())
        disconnected = []
        tristrips = bytearray()
        face_point_count = 0
        found_connections = False
        # find the tri to start at
        while len(queue):
            start = queue.pop(0)
            if start.connection_count > 0:
                found_connections = True
            disconnected.append(start)
        # now try to generate strip
        while found_connections:
            strip = start.create_strip()
            if strip:
                face_point_count += encode_triangle_strip(strip, fmt_str, tristrips)
                TriangleSet.triangles_in_strips_count += len(strip) - 2
            else:
                disconnected.append(start)
            try:
                start = queue.pop(0)
            except IndexError:
                break
        face_point_count += encode_triangles(disconnected, fmt_str, tristrips)
        print('Total tristrip triangles {}'.format(self.triangles_in_strips_count))
        return tristrips, len(self.triangles), face_point_count


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

    @staticmethod
    def nextI(currentI):
        return currentI + 1 if currentI < 2 else 0

    # def get_opposite_vert(self, edge):
    #     i = self.edges.index(edge)
    #     return self.vertices[i - 1]

    # def get_adjacent_opposite_vert(self):  # gets any adjacent tri
    #     edges = self.edges
    #     for i in range(3):
    #         edge = edges[i]
    #         if edge:
    #             edges[i] = None  # used this connection, drop it
    #             return edge.get_adjacent()

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
                adjacent.extend_right(vert_strip, (vert_strip[2], vert_strip[3]))
                return self.extend_left(vert_strip, (vert_strip[0], vert_strip[1]))
                # return vert_strip

    def extend_right(self, strip, last_edge):
        last_edge = self.edge_map[last_edge]
        if not last_edge:
            return strip
        adj = last_edge.get_adjacent(self)
        adj.disconnect()
        right_edge = adj.get_next_edge(last_edge)
        strip.append(right_edge[1])
        return adj.extend_right(strip, right_edge)

    def extend_left(self, strip, last_edge):
        last_edge = self.edge_map[last_edge]
        if not last_edge:
            return strip
        adj = last_edge.get_adjacent(self)
        adj.disconnect()
        left_edge = adj.get_next_edge(last_edge)
        strip.appendleft(left_edge[1])
        return adj.extend_left(strip, left_edge)
