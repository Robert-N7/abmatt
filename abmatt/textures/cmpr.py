"""Cmpr Tex0 format"""
from PIL import Image
from abmatt.textures.tex0 import Tex0

class Cmpr(Tex0):
    def __init__(self, name, parent):
        self.format = 14
        super(Cmpr, self).__init__(name, parent)

    def encode(self, img_file, num_mips):
        im = Image.open(img_file, 'r')
        width, height = im.size
        im = self.fix_size(im, width, height)
        block_width=4
        block_height=4
        pixels = im.load()
        # for i in range(width):
        #     for j in range(height):


    def decode(self, img_file):
        pass