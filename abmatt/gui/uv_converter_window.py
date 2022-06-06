from PyQt5.QtWidgets import QHBoxLayout, QWidget, QLineEdit, QSpinBox, QLabel, QCheckBox

from abmatt.converters import convert_obj
from abmatt.gui.converter_window import ConverterWindow


class UvConverterWindow(ConverterWindow):
    allowed_sources = ('.brres', '.obj')
    allowed_destinations = ('.brres', '.obj')

    def init_body_ui(self):
        self.vlayout.addWidget(QLabel('''
OBJ only supports one UV channel, whereas DAE can export all at once. This converter provides a solution to that, 
by importing/exporting UV Channels individually in existing polygons. If replace is checked (import only), the 
existing UV channel will be replaced. Otherwise, all other UV channels will be shifted as needed.  
        '''))
        super().init_body_ui()
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(QLabel('UV Channel'))
        self.uv_channel = QSpinBox()
        self.uv_channel.setMinimum(-1)
        self.uv_channel.setMaximum(7)
        self.uv_channel.setValue(-1)
        self.replace = QCheckBox('Replace')
        self.hlayout.addWidget(self.uv_channel)
        self.hlayout.addWidget(self.replace)
        widget = QWidget()
        widget.setLayout(self.hlayout)
        self.vlayout.addWidget(widget)
        self.setWindowTitle('OBJ UV Channels')

    def export_model(self, dest, brres_name, mdl0_name, include, exclude):
        self.handler.export_file(
            dest,
            brres_name=brres_name,
            mdl0_name=mdl0_name,
            include=include,
            exclude=exclude,
            uv_channel=self.uv_channel.value()
        )

    def import_model(self, fname, brres_name, mdl0_name, include, exclude):
        brres, polygons = self.get_brres_polygons(brres_name, mdl0_name, include, exclude)
        self.handler.converter.enqueue(convert_obj.UVImporter(
            brres,
            fname,
            polygons,
            self.uv_channel.value(),
            self.replace.isChecked()
        ))

