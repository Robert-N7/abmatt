from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QComboBox, QGridLayout, \
    QFrame, QDockWidget


class PolyEditor(QWidget):
    def __init__(self, parent, poly=None):
        super().__init__(parent)
        self.__init_ui()
        if poly is not None:
            self.on_update_poly(poly)

    def on_update_polygon(self, poly):
        self.poly = poly
        self.name_label.setText(poly.name)
        self.material_box.setText(poly.get_material().name)
        self.uv_count.setText(str(poly.num_tex))
        self.face_count.setText(str(poly.face_count))
        self.face_point_count.setText(str(poly.facepoint_count))
        self.vertex_colors.setChecked(poly.num_colors > 0)
        self.normals.setChecked(poly.has_normals())

    def __init_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)
        # Left side
        label = QLabel('Polygon:')
        material_label = QLabel('Material:', self)
        uv_label = QLabel('UV Count:', self)
        facepoint_label = QLabel('Facepoint Count:', self)
        face_label = QLabel('Face Count:', self)
        self.vertex_colors = QCheckBox('Vertex Colors', self)
        self.normals = QCheckBox('Normals', self)
        self.vertex_colors.setEnabled(False)
        self.normals.setEnabled(False)
        layout.addWidget(label)
        layout.addWidget(material_label)
        layout.addWidget(uv_label)
        layout.addWidget(facepoint_label)
        layout.addWidget(face_label)
        layout.addWidget(self.vertex_colors)
        layout.addWidget(self.normals)

        # Right side
        self.name_label = QLineEdit(self)
        self.name_label.setReadOnly(True)
        self.material_box = QLineEdit(self)
        self.material_box.setReadOnly(True)
        self.uv_count = QLineEdit(self)
        self.uv_count.setReadOnly(True)
        self.face_point_count = QLineEdit()
        self.face_point_count.setReadOnly(True)
        self.face_count = QLineEdit()
        self.face_count.setReadOnly(True)
        layout.addWidget(self.name_label, 0, 1)
        layout.addWidget(self.material_box, 1, 1)
        layout.addWidget(self.uv_count, 2, 1)
        layout.addWidget(self.face_point_count, 3, 1)
        layout.addWidget(self.face_count, 4, 1)

