import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QComboBox, \
    QFileDialog

from brres import Brres
from command import Command
from converters.convert_lib import Converter


class ConverterWindow(QWidget):
    def __init__(self, handler):
        super(ConverterWindow, self).__init__()
        self.brres = self.mdl0 = None
        self.handler = handler
        self.hlayout = QHBoxLayout()
        self.vlayout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.center_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        # File/Dest Include/Exclude
        self.left_layout.addWidget(QLabel('Convert file: '))
        self.left_layout.addWidget(QLabel('To file: '))
        self.left_layout.addWidget(QLabel('Model: '))
        self.left_layout.addWidget(QLabel('Include Polygons:'))
        self.left_layout.addWidget(QLabel('Exclude Polygons: '))
        self.file_edit = QLineEdit()
        self.dest_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.include_edit = QLineEdit()
        self.exclude_edit = QLineEdit()
        self.center_layout.addWidget(self.file_edit)
        self.center_layout.addWidget(self.dest_edit)
        self.center_layout.addWidget(self.model_edit)
        self.center_layout.addWidget(self.include_edit)
        self.center_layout.addWidget(self.exclude_edit)
        self.file_browse = QPushButton('Browse')
        self.dest_browse = QPushButton('Browse')
        self.model_select = QComboBox()
        self.include_select = QComboBox()
        self.exclude_select = QComboBox()
        self.file_browse.clicked.connect(self.browse_file)
        self.dest_browse.clicked.connect(self.browse_dest)
        self.model_select.currentTextChanged.connect(self.on_model_select)
        self.include_select.currentTextChanged.connect(self.include_changed)
        self.exclude_select.currentTextChanged.connect(self.exclude_changed)
        self.right_layout.addWidget(self.file_browse)
        self.right_layout.addWidget(self.dest_browse)
        self.right_layout.addWidget(self.model_select)
        self.right_layout.addWidget(self.include_select)
        self.right_layout.addWidget(self.exclude_select)

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

        # Buttons
        self.button_submit = QPushButton('&Convert!')
        self.button_cancel = QPushButton('C&ancel')
        self.button_submit.clicked.connect(self.submit)
        self.button_cancel.clicked.connect(self.close)
        self.button_layout.addWidget(self.button_cancel)
        self.button_layout.addWidget(self.button_submit)

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
        widget = QWidget()
        widget.setLayout(self.button_layout)
        self.vlayout.addWidget(widget)
        self.setLayout(self.vlayout)
        self.setWindowTitle('Advanced Converter')

    def submit(self):
        file = self.file_edit.text()
        dest = self.dest_edit.text()
        name, file_ext = os.path.splitext(file)
        name, dest_ext = os.path.splitext(dest)
        file_ext = file_ext.lower()
        dest_ext = dest_ext.lower()
        valid_ext = ['.brres', '.obj', '.dae']
        if file_ext not in valid_ext or dest_ext not in valid_ext:
            self.handler.error(f'File extension must be {", ".join(valid_ext)}')
            return
        elif file_ext == dest_ext:
            self.handler.error(f'Converter destination must have different extension.')
            return
        model = self.model_edit.text()
        include = self.include_edit.text()
        if include:
            include = [x.strip() for x in include.split(',')]
        exclude = self.exclude_edit.text()
        if exclude:
            exclude = [x.strip() for x in exclude.split(',')]
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
        if file_ext == '.brres':
            self.handler.open(file)
            self.handler.export_file(
                dest, brres_name=file, mdl0_name=model, include=include, exclude=exclude, flags=flags
            )
        else:
            self.handler.open(dest)
            self.handler.import_file(
                file, brres_name=dest, mdl0_name=model, include=include, exclude=exclude, flags=flags
            )

    def on_brres_select(self, name):
        fname, ext = os.path.splitext(name)
        if ext == '.brres':
            brres = Brres.get_brres(name)
            if brres:
                self.brres = brres
                self.model_select.clear()
                self.model_select.addItems([x.name for x in brres.models])

    def browse_file(self):
        name, filter = QFileDialog.getOpenFileName(
            self, 'Convert File', self.handler.cwd, 'Model Files (*.brres *.obj *.dae)'
        )
        if name:
            self.file_edit.setText(name)
            self.on_brres_select(name)

    def browse_dest(self):
        name, filter = QFileDialog.getSaveFileName(
            self, 'Convert File', self.handler.cwd, 'Model Files (*.brres *.obj *.dae)'
        )
        if name:
            self.dest_edit.setText(name)
            self.on_brres_select(name)

    def on_model_select(self):
        model_name = self.model_select.currentText()
        self.model_edit.setText(model_name)
        if self.brres:
            self.mdl0 = self.brres.get_model(model_name)
            polygons = ['']
            polygons.extend([x.name for x in self.mdl0.objects])
            self.include_select.clear()
            self.exclude_select.clear()
            self.include_select.addItems(polygons)
            self.exclude_select.addItems(polygons)

    def include_changed(self):
        current = self.include_edit.text()
        new = self.include_select.currentText()
        current = current + ', ' + new if current else new
        self.include_edit.setText(current)

    def exclude_changed(self):
        current = self.exclude_edit.text()
        new = self.exclude_select.currentText()
        current = current + ', ' + new if current else new
        self.exclude_edit.setText(current)
