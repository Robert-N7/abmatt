from abmatt.autofix import AutoFix
from abmatt.brres.lib.decoder import ColorDecoder
from abmatt.brres.lib.node import Node

# Constants
FMT_RGB565 = 0
FMT_RGB8 = 1
FMT_RGBX8 = 2
FMT_RGBA4 = 3
FMT_RGBA6 = 4
FMT_RGBA8 = 5


class Color(Node):

    def __init__(self, name, parent, binfile=None):
        self.decoded = None
        super().__init__(name, parent, binfile)

    def begin(self):
        self.flags = 0
        self.index = 0
        self.count = 0
        self.format = FMT_RGB8
        self.has_alpha = False
        self.stride = 3
        self.flags = 0

    def get_decoded(self):
        if self.decoded is None:
            self.decoded = ColorDecoder.decode_data(self)
        return self.decoded

    def __iter__(self):
        return iter(self.get_decoded())

    def __next__(self):
        return next(self.decoded)

    def __getitem__(self, item):
        return self.get_decoded()[item]

    def check(self):
        if not FMT_RGB565 <= self.format <= FMT_RGBA8:
            AutoFix.get().error(f'Color {self.name} has unknown color format.')
            self.format = 0

    def set_format(self, fmt):
        self.format = fmt
        if fmt < FMT_RGBA4:
            self.stride = fmt + 2
            self.has_alpha = False
        else:
            self.stride = fmt - 1
            self.has_alpha = True

    def get_format(self):
        return self.format

    def get_has_alpha(self):
        return self.has_alpha

    def get_stride(self):
        return self.stride

    def get_flags(self):
        return self.flags

    def __len__(self):
        return self.count


