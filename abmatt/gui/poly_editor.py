from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QComboBox, QGridLayout, \
    QFrame, QDockWidget

from gui.brres_path import BrresPath, NotABrresError


class PolyEditor(QFrame):
    def __init__(self, parent, poly=None):
        super().__init__(parent)
        self.__init_ui()
        if poly is not None:
            self.on_update_poly(poly)
        else:
            self.poly = None

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
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setLineWidth(2)
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

        # Right side
        self.name_label = QLabel(self)
        # self.name_label.setReadOnly(True)
        self.material_box = QLabel(self)
        # self.material_box.setReadOnly(True)
        self.uv_count = QLabel(self)
        # self.uv_count.setReadOnly(True)
        self.face_point_count = QLabel()
        # self.face_point_count.setReadOnly(True)
        self.face_count = QLabel()
        # self.face_count.setReadOnly(True)
        layout.addWidget(self.name_label, 0, 1)
        layout.addWidget(self.material_box, 1, 1)
        layout.addWidget(self.uv_count, 2, 1)
        layout.addWidget(self.face_point_count, 3, 1)
        layout.addWidget(self.face_count, 4, 1)
        layout.addWidget(self.vertex_colors, 5, 1)
        layout.addWidget(self.normals, 6, 1)
        self.setAcceptDrops(True)

    @staticmethod
    def get_material_from_text(text, trace_path=False):
        try:
            bp = BrresPath(path=text)
            b, m, mat = bp.split_path()
            return mat if not mat or not trace_path else bp.trace_path(b, m, mat)[2]
        except NotABrresError as e:
            return False

    def dragEnterEvent(self, a0):
        data = a0.mimeData()
        if self.poly and data.hasText() \
                and self.get_material_from_text(data.text()):
            a0.accept()
        else:
            a0.ignore()

    def dragMoveEvent(self, a0):
        data = a0.mimeData()
        if self.poly and data.hasText() \
                and self.get_material_from_text(data.text()):
            a0.accept()
        else:
            a0.ignore()

    def dropEvent(self, a0):
        data = a0.mimeData()
        if self.poly and data.hasText():
            mat = self.get_material_from_text(data.text(), trace_path=True)
            if mat:
                a0.accept()
                self.poly.set_material(mat)
                self.material_box.setText(mat.name)
                return
        a0.ignore()