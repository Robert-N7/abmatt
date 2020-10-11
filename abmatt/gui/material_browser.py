from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QGridLayout, QScrollArea, QSizePolicy, QPushButton, QTableWidget, \
    QVBoxLayout, QLabel, QHBoxLayout, QTabWidget, QCheckBox


class MaterialTabs(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        # Material selection tabs
        tab_widget = QTabWidget(self)
        layout.addWidget(tab_widget)
        self.material_library = MaterialBrowser(self)
        tab_widget.addTab(self.material_library, 'Library Materials')
        self.scene_library = MaterialBrowser(self, True)
        tab_widget.addTab(self.scene_library, 'Scene Materials')
        self.setLayout(layout)

    def __init_material_editor(self, layout):
        # Material edit tab
        widget = QWidget()
        layout.addWidget(widget)
        grid = QGridLayout()
        widget.setLayout(grid)
        # Left
        name_label = QLabel('Material:')
        cull_label = QLabel('Cull:')
        trans_label = QLabel('Transparency threshold:')
        color_label = QLabel('Color:')
        self.blend = QCheckBox('Blend')
        maps = QLabel('Maps:')
        grid.addWidget(name_label)
        grid.addWidget(cull_label)
        grid.addWidget(trans_label)
        grid.addWidget(color_label)
        grid.addWidget(self.blend)
        grid.addWidget(maps)
        # Right


    def add_brres_materials_to_scene(self, brres):
        self.scene_library.add_brres_materials(brres)

    def add_materials_to_library(self, materials):
        library = self.material_library.materials
        for x in materials:
            self.material_library.add_material(x, library)

    def add_material_to_library(self, material):
        self.material_library.add_material(material, self.material_library.materials)


class MaterialBrowser(QWidget):
    def __init__(self, parent, use_absolute_path=False):
        super().__init__(parent)
        self.use_absolute_path = use_absolute_path
        self.init_UI()
        self.grid_col_max = 4
        self.materials = {}

    def init_UI(self):
        # self.group = QGroupBox('Materials', self)
        content = QWidget()
        self.grid = QGridLayout(self)
        self.grid_row = self.grid_col = 0
        content.setLayout(self.grid)
        self.scroll_area = QScrollArea(self)
        # self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(content)
        self.horz_layout = QHBoxLayout()
        self.horz_layout.addWidget(self.scroll_area)
        self.setLayout(self.horz_layout)

    def add_brres_materials(self, brres):
        if self.use_absolute_path:
            materials = self.materials.get(brres.name)
            if materials is None:
                self.materials[brres.name] = materials = {}
        else:
            materials = self.materials
        for model in brres.models:
            for material in model.materials:
                self.add_material(material, materials)

    def increment_grid(self):
        row = self.grid_row
        col = self.grid_col
        if col >= self.grid_col_max - 1:
            self.grid_col = 0
            self.grid_row += 1
        else:
            self.grid_col += 1
        return row, col

    def add_material(self, material, materials):
        name = material.name
        if name not in materials:
            materials[name] = material
            label = QLabel(material.name)
            # label.setFixedWidth(120)
            self.grid.addWidget(label, *self.increment_grid())