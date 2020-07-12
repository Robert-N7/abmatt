#!/usr/bin/python
""" OBJ File Format
    Author: Robert Nelson
"""
import os

from model_formats.geometry import MdlFile, Vertex, UV, Normal, PSVertex, FacePoint, Face, Line, Object, Group


def get_one_based_index(i):
    return i + 1 if i >= 0 else i


class Obj(MdlFile):

    def __init__(self, filename):
        super(Obj, self).__init__(filename)
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.ps_vertices = []
        self.faces = []
        self.lines = []
        self.mtllib = []
        self.objects = []
        self.groups = []

    def parse(self):
        current_object = current_group = None
        data = self._parse()
        for x in data:
            if x and x[0] != '#':
                words = x.split()
                start = words.pop(0)
                if start == 'v':    # vertex
                    w = words[3] if len(words) > 3 else 1
                    self.vertices.append(Vertex(words[0], words[1], words[2], w))
                elif start == 'vt':
                    if len(words) > 1:
                        v = words[1]
                        w = words[2] if len(words) > 3 else 0
                    else:
                        v = w = 0
                    self.uvs.append(UV(words[0], v, w))
                elif start == 'vn':
                    self.normals.append(Normal(words[0], words[1], words[2]))
                elif start == 'vp':
                    if len(words) > 2:
                        v = words[1]
                        w = words[2] if len(words) > 3 else 0
                    else:
                        v = w = 0
                    self.ps_vertices.append(PSVertex(words[0], v, w))
                elif start == 'f':      # face
                    face = Face()
                    for x in words:
                        fp_data = x.split('/')
                        uv = normal = None
                        t = int(fp_data.pop(0)[-1])
                        vertex = self.vertices[get_one_based_index(t)]
                        if len(fp_data):
                            t = int(fp_data.pop(0)[-1])
                            if t != '':
                                uv = self.uvs[get_one_based_index(t)]
                            if len(fp_data):
                                normal = self.normals[get_one_based_index(int(fp_data.pop(0)[-1]))]
                        face.add_point(FacePoint(vertex, uv, normal))
                    if current_group:
                        current_group.add_face(face)

                elif start == 'l':      # line
                    line = Line()
                    for x in words:
                        line.add_vertex(self.vertices[get_one_based_index(x[-1])])
                    self.lines.append(line)
                elif start == 'mtllib':
                    self.mtllib.append(words.pop(0))
                elif start == 'o':
                    current_object = Object(words[0])
                    self.objects.append(current_object)
                elif start == 'g':
                    current_group = Group(words[0])
                    self.groups.append(current_group)
                    if current_object:
                        current_object.add_group(current_group)
                elif start == 'usemtl':
                    current_group.set_material(words[0])
                elif start == 's':
                    current_group.set_smooth(words[0] != 'off')

    def export(self):
        # header
        mtllib = os.path.splitext(self.filename)[0] + '.mtl'
        data = "# Created with ANoob's Brres Material Editor\n"
        data += 'mtllib ' + mtllib + '\n'
        for x in self.groups:
            data += 'g ' + x.name
            if x.material:
                data += 'usemtl ' + x.material + '\n'
            

        self._export(data)
