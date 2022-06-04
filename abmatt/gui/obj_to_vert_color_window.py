from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget, QCheckBox

from brres import Brres
from converters import convert_obj
from gui.color_widget import ColorWidget
from gui.converter_window import ConverterWindow


class ObjToVertColorWindow(ConverterWindow):
    allowed_sources = ('.obj', '.brres')
    allowed_destinations = ('.brres', '.obj')

    def __init__(self, handler):
        super().__init__(handler)

    def init_body_ui(self):
        self.vlayout.addWidget(QLabel('''How it works:
Imports:
Since OBJ does not support vertex colors, this provides an alternative way to import vertex colors. 
The vertex color is computed by using the material(s) diffuse color (kD + dissolve in .mtl) 
of the similar triangle connected to the matching vertex. If no matching vertex is found, 
the default color is used. If overwrite is specified, it will overwrite existing colors in polygons.

Exports:
Creates three small triangles from each triangle, each corresponding to a vertex color.
'''))
        super().init_body_ui()
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(QLabel('Default Color:'))
        self.color_widget = ColorWidget((170, 170, 170, 255))
        self.hlayout.addWidget(self.color_widget)
        widget = QWidget()
        widget.setLayout(self.hlayout)
        self.overwrite = QCheckBox('Overwrite Existing')
        self.vlayout.addWidget(self.overwrite)
        self.vlayout.addWidget(widget)
        self.setWindowTitle('OBJ Vertex Colors')

    def export_model(self, dest, brres_name, mdl0_name, include, exclude):
        polygons = self.get_brres_polygons(brres_name, mdl0_name, include, exclude)
        convert_obj.vertex_colors_to_obj(
            polygons, dest
        )

    def get_brres_polygons(self, brres_name, mdl0_name, include, exclude):
        brres = Brres.get_brres(brres_name)
        mdl = brres.get_model(mdl0_name)
        polygons = [
            x for x in mdl.objects
            if (not include or x.name in include) and x.name not in exclude
        ]
        return polygons

    def import_model(self, fname, brres_name, mdl0_name, include, exclude):
        polygons = self.get_brres_polygons(brres_name, mdl0_name, include, exclude)
        convert_obj.obj_mats_to_vertex_colors(
            polygons,
            fname,
            self.color_widget.color,
            self.overwrite.isChecked()
        )

