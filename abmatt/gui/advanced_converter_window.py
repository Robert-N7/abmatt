from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QCheckBox

from abmatt.converters.convert_lib import Converter
from abmatt.gui.converter_window import ConverterWindow


class AdvancedConverterWindow(ConverterWindow):
    def __init__(self, handler):
        super().__init__(handler)

    def init_body_ui(self):
        super().init_body_ui()
        self.hlayout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.center_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        # Flags
        self.exclude_norm_cb = QCheckBox('No Normals')
        self.exclude_colors_cb = QCheckBox('No Colors')
        self.exclude_uvs_cb = QCheckBox('No UVs')
        self.patch_cb = QCheckBox('Patch Existing Model (Import Only)')
        self.single_bone_cb = QCheckBox('Use Single Bone')
        self.moonview_cb = QCheckBox('Moonview Highway (Import Only)')
        self.left_layout.addWidget(self.exclude_norm_cb)
        self.left_layout.addWidget(self.exclude_colors_cb)
        self.left_layout.addWidget(self.exclude_uvs_cb)
        self.center_layout.addWidget(self.patch_cb)
        self.center_layout.addWidget(self.single_bone_cb)
        self.center_layout.addWidget(self.moonview_cb)
        widget = QWidget()
        widget.setLayout(self.left_layout)
        self.hlayout.addWidget(widget)
        widget = QWidget()
        widget.setLayout(self.center_layout)
        self.hlayout.addWidget(widget)
        widget = QWidget()
        widget.setLayout(self.right_layout)
        self.hlayout.addWidget(widget)
        widget = QWidget()
        widget.setLayout(self.hlayout)
        self.vlayout.addWidget(widget)
        self.setWindowTitle('Advanced Converter')

    def get_flags(self):
        flags = 0
        if self.exclude_norm_cb.isChecked():
            flags |= Converter.NO_NORMALS
        if self.exclude_uvs_cb.isChecked():
            flags |= Converter.NO_UVS
        if self.exclude_colors_cb.isChecked():
            flags |= Converter.NO_COLORS
        if self.single_bone_cb.isChecked():
            flags |= Converter.SINGLE_BONE
        if self.patch_cb.isChecked():
            flags |= Converter.PATCH
        if self.moonview_cb.isChecked():
            flags |= Converter.MOONVIEW
        return flags

    def export_model(self, dest, brres_name, mdl0_name, include, exclude):
        self.handler.export_file(
            dest, brres_name=brres_name, mdl0_name=mdl0_name,
            include=include, exclude=exclude, flags=self.get_flags()
        )

    def import_model(self, fname, brres_name, mdl0_name, include, exclude):
        self.handler.import_file(
            fname, brres_name, mdl0_name=mdl0_name,
            include=include, exclude=exclude, flags=self.get_flags()
        )
