#!/usr/bin/python
"""
Various classes dealing with model geometry
"""


class MdlFile:
    def __init__(self, filename):
        self.filename = filename

    def _parse(self):
        data = ""
        with open(self.filename, 'r') as file:
            data = file.readlines()
        return data

    def parse(self):
        pass

    def _export(self, data):
        with open(self.filename, 'w') as file:
            file.write(data)

    def export(self):
        pass


class Vertex:
    def __init__(self, x, y, z, w=1):
        self.x = x
        self.y = y
        self.z = z
        self.w = w


class PSVertex:
    def __init__(self, u, v=0, w=0):
        self.u = u
        self.v = v
        self.w = w


class UV:
    def __init__(self, u, v=0, w=0):
        self.u = u
        self.v = v
        self.w = w


class Normal:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class FacePoint:
    def __init__(self, vertex, uv=None, normal=None):
        self.vertex = vertex
        self.uv = uv
        self.normal = normal


class Face:
    def __init__(self, face_points=None):
        self.face_points = face_points if face_points else []

    def add_point(self, fp):
        self.face_points.append(fp)


class Line:
    def __init__(self, vertices=None):
        self.vertices = vertices if vertices else []

    def add_vertex(self, vertex):
        self.vertices.append(vertex)


class Group:
    def __init__(self, name, material=None, smooth=False):
        self.name = name
        self.material = material
        self.smooth = smooth
        self.faces = []

    def add_face(self, face):
        self.faces.append(face)

    def set_smooth(self, bool):
        self.smooth = bool

    def set_material(self, material):
        self.material = material


class Object:
    def __init__(self, name, group=None):
        self.name = name
        self.groups = []
        if group:
            self.groups.append(group)

    def add_group(self, group):
        self.groups.append(group)
