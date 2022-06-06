from PyQt5.QtWidgets import QCheckBox, QLabel, QGridLayout, \
    QFrame, QSpinBox, QPushButton

from abmatt.brres.lib.node import ClipableObserver
from abmatt.gui.brres_path import BrresPath
from abmatt.gui.mat_widget import MaterialWidget, MatWidgetHandler
from abmatt.gui.material_editor import MaterialContainer


class PolyEditor(QFrame, ClipableObserver, MatWidgetHandler):
    def on_material_select(self, material):
        self.handler.on_material_select(material)

    def on_material_edit(self, material):
        mat_editor = MaterialContainer(material=material)

    def on_material_remove(self, material):
        pass

    def on_node_update(self, node):
        self.on_update_polygon(node)

    def __init__(self, parent, poly=None):
        super().__init__(parent)
        self.handler = parent
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
        diff = poly != self.poly
        if diff:
            if self.poly:
                self.poly.unregister(self)
            self.poly = poly
        if poly:
            self.name_label.setText(poly.name)
            uv_count = poly.count_uvs()
            self.uv_count.setText(str(uv_count))
            self.uv_channel_edit.setMaximum(uv_count - 1 if uv_count else 0)
            self.uv_remove_btn.setEnabled(bool(uv_count))
            self.face_count.setText(str(poly.face_count))
            self.face_point_count.setText(str(poly.facepoint_count))
            has_colors = poly.count_colors() > 0
            self.vertex_colors.setChecked(has_colors)
            self.colors_remove_btn.setEnabled(has_colors)
            has_normals = poly.has_normals()
            self.normals.setChecked(has_normals)
            self.normals_remove_btn.setEnabled(has_normals)
            self.material_box.set_material(poly.get_material())
            self.enable_mat_drag = enable_edits
            self.material_box.set_material(poly.get_material())
            if diff:
                poly.register_observer(self)
        else:
            self.name_label.setText('Null')
            self.uv_count.setText('0')
            self.face_count.setText('0')
            self.face_point_count.setText('0')
            self.vertex_colors.setChecked(False)
            self.normals.setChecked(False)
            self.material_box.set_material(None)
            self.enable_mat_drag = False
            self.normals_remove_btn.setEnabled(False)
            self.uv_remove_btn.setEnabled(False)
            self.colors_remove_btn.setEnabled(False)

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
        self.uv_channel_edit = QSpinBox(self)
        self.uv_channel_edit.setMinimum(0)
        self.uv_channel_edit.setMaximum(7)
        layout.addWidget(label)
        layout.addWidget(material_label)
        layout.addWidget(uv_label)
        layout.addWidget(self.uv_channel_edit)
        layout.addWidget(facepoint_label)
        layout.addWidget(face_label)
        layout.addWidget(self.vertex_colors)
        layout.addWidget(self.normals)

        # Right side
        self.name_label = QLabel(self)
        self.material_box = MaterialWidget(self, handler=self, width=128)
        self.uv_count = QLabel(self)
        self.uv_remove_btn = QPushButton('Remove UV Channel', self)
        self.uv_remove_btn.clicked.connect(self.remove_uv)
        self.face_point_count = QLabel(self)
        self.face_count = QLabel(self)
        self.normals_remove_btn = QPushButton('Remove Normals', self)
        self.normals_remove_btn.clicked.connect(self.remove_normals)
        self.colors_remove_btn = QPushButton('Remove Vertex Color', self)
        self.colors_remove_btn.clicked.connect(self.remove_vertex_colors)
        layout.addWidget(self.name_label, 0, 1)
        layout.addWidget(self.material_box, 1, 1)
        layout.addWidget(self.uv_count, 2, 1)
        layout.addWidget(self.uv_remove_btn, 3, 1)
        layout.addWidget(self.face_point_count, 4, 1)
        layout.addWidget(self.face_count, 5, 1)
        layout.addWidget(self.colors_remove_btn, 6, 1)
        layout.addWidget(self.normals_remove_btn, 7, 1)
        self.normals_remove_btn.setEnabled(False)
        self.colors_remove_btn.setEnabled(False)
        self.uv_remove_btn.setEnabled(False)
        self.setAcceptDrops(True)

    def remove_uv(self):
        uv_channel = self.uv_channel_edit.value()
        decoded = self.poly.get_decoded()
        if len(decoded.texcoords) > uv_channel:
            decoded.texcoords.pop(uv_channel)
        decoded.recode(self.poly)

    def remove_vertex_colors(self):
        if self.poly.has_color0():
            decoded = self.poly.get_decoded()
            decoded.colors = None
            decoded.recode(self.poly)

    def remove_normals(self):
        if self.poly.normals:
            decoded = self.poly.get_decoded()
            decoded.normals = None
            decoded.recode(self.poly)

    def dragEnterEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText() \
                and self.handler.locate_material(BrresPath(data.text())):
            a0.accept()
        else:
            a0.ignore()

    def dragMoveEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText() \
                and self.handler.locate_material(BrresPath(data.text())):
            a0.accept()
        else:
            a0.ignore()

    def dropEvent(self, a0):
        data = a0.mimeData()
        if self.enable_mat_drag and self.poly and data.hasText():
            text = data.text()
            mat = self.handler.locate_material(BrresPath(text))
            # mat = get_material_by_url(text, trace_path=True)
            if mat:
                a0.accept()
                self.poly.material.paste(mat)
                # self.poly.set_material(mat)
                return
        a0.ignore()
