from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtWidgets import QLabel

from brres.lib.node import ClipableObserver
from gui.brres_path import BrresPath
from gui.image_manager import ImageObserver, ImageManager, update_image


class MatWidgetHandler:
    def on_material_select(self, material):
        raise NotImplementedError()


class MaterialWidget(QLabel, ClipableObserver, ImageObserver):
    def on_image_update(self, dir):
        self.layer_name = name = self.material.get_first_layer_name()
        if name:
            self.__update_image(dir, name)

    def on_node_update(self, node):
        self.on_child_update(node)  # redirect

    def on_child_update(self, child):
        name = self.material.get_first_layer_name()
        if name != self.layer_name:
            self.__update_image(ImageManager.get().get_image_dir(self.material.parent.parent), name)

    def __update_image(self, dir, name):
        update_image(self, dir, name)
        # img_file = os.path.join(dir, name + '.png')
        # if os.path.exists(img_file):
        #     pixelmap = QPixmap(img_file).scaledToWidth(64)
        #     self.setPixmap(pixelmap)
        #     self.setMask(pixelmap.mask())

    def __init__(self, parent, handler=None, material=None, brres_path=None):
        super().__init__(parent)
        self.handler = handler
        self.layer_name = None
        self.is_text = True
        self.material = None
        if material is not None:
            self.set_material(material, brres_path)

    def set_material(self, material, brres_path=None):
        if self.material is not None:
            ImageManager.get().unsubscribe(self, self.material.parent.parent)
            self.material.unregister(self)
        self.material = material
        self.setToolTip(material.name)
        self.setText(material.name)
        self.is_text = True
        self.material.register_observer(self)
        ImageManager.get().subscribe(self, material.parent.parent)

        if brres_path is None:
            self.brres_path = BrresPath(material=material)
        else:
            self.brres_path = brres_path


    def mousePressEvent(self, ev):
        if self.handler:
            self.handler.on_material_select(self.material)
        if ev.button() == Qt.LeftButton:
            self.drag_start_position = ev.pos()

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
