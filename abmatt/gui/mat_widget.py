from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtWidgets import QLabel, QAction, QWidget, QVBoxLayout

from abmatt.brres.lib.node import ClipableObserver
from abmatt.gui.brres_path import BrresPath
from abmatt.gui.image_manager import ImageObserver, ImageManager, update_image


class MatWidgetHandler:
    def should_remove_unused_mats(self):
        return True

    def on_material_select(self, material):
        raise NotImplementedError()

    def on_material_edit(self, material):
        raise NotImplementedError()

    def on_material_remove(self, material):
        raise NotImplementedError()


class MaterialWidget(QWidget, ClipableObserver, ImageObserver):
    def on_image_update(self, dir):
        self.layer_name = name = self.material.get_first_layer_name()
        if name:
            self.__update_image(dir, name)

    def on_node_update(self, node):
        self.on_child_update(node)  # redirect
        if node is self.material:
            if self.handler.should_remove_unused_mats() and not node.is_used():
                self.remove_material()

    def on_child_update(self, child):
        name = self.material.get_first_layer_name()
        if name != self.layer_name:
            self.__update_image(ImageManager.get().get_image_dir(self.material.getBrres()), name)

    def __update_image(self, dir, name):
        if not update_image(self.img_label, dir, name, scale_width=self.w):
            pass

    def __init__(self, parent, handler=None, material=None, brres_path=None, removable=False, width=64):
        super().__init__(parent)
        self.handler = handler
        self.__init_ui()
        self.layer_name = None
        self.material = None
        self.removable = removable
        self.w = width
        if material is not None:
            self.set_material(material, brres_path)
        self.__init_context_menu()

    def __init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.text_label = QLabel(self)
        self.img_label = QLabel(self)
        self.main_layout.addWidget(self.text_label)
        self.main_layout.addWidget(self.img_label)
        self.setLayout(self.main_layout)

    def __del__(self):
        if self.material is not None:
            self.material.unregister(self)

    def __init_context_menu(self):
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        edit_action = QAction('Edit', self)
        edit_action.triggered.connect(self.edit_material)
        self.addAction(edit_action)
        if self.removable:
            remove_action = QAction('Remove', self)
            remove_action.triggered.connect(self.remove_material)
            self.addAction(remove_action)

    def remove_material(self):
        ImageManager.get().unsubscribe(self, self.material.parent.parent)
        self.handler.on_material_remove(self.material)
        self.setParent(None)

    def edit_material(self):
        self.handler.on_material_edit(self.material)

    def set_material(self, material, brres_path=None):
        if self.material is not None:
            ImageManager.get().unsubscribe(self, self.material.parent.parent)
            self.material.unregister(self)
        self.material = material
        if brres_path is None:
            self.brres_path = BrresPath(material=material)
        else:
            self.brres_path = brres_path
        if material is not None:
            self.setToolTip(self.brres_path.get_path())
            self.text_label.setText(material.name)
            self.material.register_observer(self)
            ImageManager.get().subscribe(self,
                                         material.parent.parent, material.get_first_layer_name())
        else:
            self.text_label.setText('Null')
            self.setToolTip('Null')


    def mousePressEvent(self, ev):
        if self.handler:
            self.handler.on_material_select(self.material)
        if ev.button() == Qt.LeftButton:
            self.drag_start_position = ev.pos()

    def mouseDoubleClickEvent(self, a0):
        self.handler.on_material_edit(self.material)

    def mouseMoveEvent(self, ev):
        if not ev.buttons() & Qt.LeftButton:
            return
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText(self.brres_path.get_path())
        drag.setMimeData(mimedata)
        pixmap = QPixmap(self.size())
        painter = QPainter(pixmap)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(ev.pos())
        drag.exec_(Qt.CopyAction | Qt.MoveAction)
