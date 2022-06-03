from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget, QCheckBox

from brres import Brres
from converters import convert_obj
from gui.color_widget import ColorWidget
from gui.converter_window import ConverterWindow


class ObjToVertColorWindow(ConverterWindow):
    allowed_sources = ('obj',)
    allowed_destinations = ('brres',)

    def __init__(self, handler):
        super().__init__(handler)

    def init_body_ui(self):
        self.vlayout.addWidget(QLabel('''How it works:
Since OBJ does not support vertex colors, this provides an alternative way to import vertex colors. 
The vertex color is computed by interpolating the material(s) diffuse color (kD + dissolve in .mtl) 
of all faces connected to the matching vertex. If no matching vertex is found, the default color
is used. 
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
        self.setWindowTitle('Create Vertex Colors from OBJ')

    def export_model(self, dest, brres_name, mdl0_name, include, exclude):
        pass

    def import_model(self, fname, brres_name, mdl0_name, include, exclude):
        brres = Brres.get_brres(brres_name)
        mdl = brres.get_model(mdl0_name)
        polygons = [x for x in mdl.objects if (not include or x.name in include) and x.name not in exclude]
        convert_obj.obj_mats_to_vertex_colors(
            polygons,
            fname,
            self.color_widget.color,
            self.overwrite.isChecked()
        )

