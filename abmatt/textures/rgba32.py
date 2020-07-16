"""Rgba32 Tex0 format"""
from abmatt.textures.tex0 import Tex0


class Rgba32(Tex0):
    def __init__(self, name, parent):
        self.format = 6
        super(Rgba32, self).__init__(name, parent)

    def encode(self, img_file, num_mips):
        pass

    def decode(self, img_file):
        pass