class ModelEncoder():
    """Abstract class that specifies how to encode model"""
    def before_encoding(self, converter):
        return

    def get_encoder(self, geometry):
        """Gets encoder corresponding to geometry"""
        raise NotImplementedError()


class GeometryEncoder():
    """Used for more fine-tuned options when encoding geometry"""
    def before_encode(self, geo):
        return

    def after_encode(self, encoded_poly):
        return

    def __init__(self):
        self.vertex_encoder = None  # PointEncoder
        self.normal_encoder = None  # PointEncoder
        self.uv_encoders = []       # PointEncoders
        self.color_encoder = None   # ColorEncoder


class ColorEncoder():
    """Abstract class specifies how colors should be encoded"""
    def before_encode(self, generic_color):
        return

    def after_encode(self, mdl0_color):
        return

    def get_format(self):
        """ Determines encoding format
        0: RGB565
        1: RGB8
        2: RGBX8
        3: RGBA4
        4: RGBA6
        5: RGBA8
        :return: int
        """
        raise NotImplementedError()

    def should_consolidate(self):
        return True


class PointEncoder():
    """Abstract class specifies how points should be encoded"""
    def before_encode(self, generic_point):
        return

    def after_encode(self, mdl0_point):
        return

    def get_format(self):
        """Point format, may be one of the following:
            b: signed byte
            B: unsigned byte
            h: signed short
            H: unsigned short
            f: float
            All except for float are encoded by multiplying the number by 2^divisor
        """
        raise NotImplementedError()

    def get_divisor(self):
        """If the format is not float, shifts the bits by (divisor) when encoding
            b: max 6, 1 sign bit
            B: max 7
            h: max 14, 1 sign bit
            H: max 15
        """
        raise NotImplementedError()

    def should_consolidate(self):
        """If enabled, the points will be consolidated to reduce space"""
        return True
