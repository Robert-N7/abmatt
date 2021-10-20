from abmatt.converters.geometry import Geometry


class EditGeometry:
    def __init__(self, polygon):
        self.polygon = polygon
        self.geometry = polygon.get_decoded()

