from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QComboBox, QGridLayout, \
    QFrame, QDockWidget

from abmatt.brres.lib.node import ClipableObserver
from abmatt.gui.brres_path import BrresPath, NotABrresError, get_material_by_url
from abmatt.gui.mat_widget import MaterialWidget, MatWidgetHandler


class PolyEditor(QFrame, ClipableObserver, MatWidgetHandler):
    def on_material_select(self, material):
        pass

    def on_material_edit(self, material):
        pass

    def on_material_remove(self, material):
        pass

    def on_node_update(self, node):
        self.on_update_polygon(node)

    def __init__(self, parent, poly=None):
        super().__init__(parent)
        self.__init_ui()
        self.enable_mat_drag = True
        if poly is not None:
            self.on_update_poly(poly)
        else:
            self.poly = None

    def on_brres_lock(self, brres):
        if self.poly and self.poly.parent.parent == brres:
            self.on_update_polygon(None)

    def on_brres_unlock(self, brres):
        if self.poly and self.poly.parent.parent == brres:
            self.enable_mat_drag = True

    def on_update_polygon(self, poly, enable_edits=True):
        if poly != self.poly:
            if self.poly:
                self.poly.unregister(self)
            self.poly = poly
            if poly:
                poly.register_observer(self)
                self.name_label.setText(poly.name)
                self.uv_count.setText(str(poly.count_uvs()))
                self.face_count.setText(str(poly.face_count))
                self.face_point_count.setText(str(poly.facepoint_count))
                self.vertex_colors.setChecked(poly.count_colors() > 0)
                self.normals.setChecked(poly.has_normals())
                self.material_box.set_material(poly.get_material())
                self.enable_mat_drag = enable_edits
            else:
                self.name_label.setText('Null')
                self.uv_count.setText('0')
                self.face_count.setText('0')
                self.face_point_count.setText('0')
                self.vertex_colors.setChecked(False)
                self.normals.setChecked(False)
                self.material_box.set_material(None)
                self.enable_mat_drag = False

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
        self.material_box = MaterialWidget(self, handler=self)
        # self.material_box.setReadOnly(True)
        self.uv_count = QLabel(self)
        # self.uv_count.setReadOnly(True)
        self.face_point_count = QLabel(self)
        # self.face_point_count.setReadOnly(True)
        self.face_count = QLabel(self)
        # self.face_count.setReadOnly(True)
        layout.addWidget(self.name_label, 0, 1)
        layout.addWidget(self.material_box, 1, 1)
        layout.addWidget(self.uv_count, 2, 1)
        layout.addWidget(self.face_point_count, 3, 1)
        layout.addWidget(self.face_count, 4, 1)
        layout.addWidget(self.vertex_colors, 5, 1)
        layout.addWidget(self.normals, 6, 1)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText() \
                and get_material_by_url(data.text()):
            a0.accept()
        else:
            a0.ignore()

    def dragMoveEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText() \
                and get_material_by_url(data.text()):
            a0.accept()
        else:
            a0.ignore()

    def dropEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText():
            text = data.text()
            mat = get_material_by_url(text, trace_path=True)
            if mat:
                a0.accept()
                self.poly.set_material(mat)
                self.material_box.set_material(mat)
                return
        a0.ignore()
