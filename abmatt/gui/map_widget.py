from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedLayout, QComboBox, QLabel

from abmatt.brres.lib.node import ClipableObserver
from abmatt.gui.image_manager import ImageObserver, update_image, ImageManager


class Tex0WidgetSubscriber:
    def on_map_change(self, tex0, index):
        raise NotImplementedError()

    def on_map_add(self, tex0):
        raise NotImplementedError()

    def on_map_remove(self, tex0):
        raise NotImplementedError()

    def on_map_replace(self, tex0):
        raise NotImplementedError()


class Tex0WidgetGroup(QWidget):
    def __init__(self, parent, tex0s=None, max_rows=0, max_columns=4, subscriber=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        self.stack = QStackedLayout(self)
        self.map_box = QComboBox()
        self.map_box.activated.connect(self.on_map_change)
        main_layout.addWidget(self.map_box)
        main_layout.addLayout(self.stack)
        self.subscriber = subscriber
        self.tex0s = []
        if tex0s is not None:
            self.add_tex0s(tex0s)
        self.setLayout(main_layout)

    def get_tex0(self, index):
        return self.tex0s[index]

    def on_map_change(self, index):
        self.stack.setCurrentIndex(index)
        if self.subscriber is not None:
            self.subscriber.on_map_change(self.tex0s[index], index)

    def reset(self):
        for i in reversed(range(self.stack.count())):
            widget = self.stack.itemAt(i).widget()
            widget.del_widget()
            self.map_box.removeItem(i)
        self.tex0s = []

    def set_tex0s(self, tex0s):
        self.reset()
        self.add_tex0s(tex0s)

    def add_tex0s(self, tex0s):
        for x in tex0s:
            widget = MapWidget(self, x)
            self.tex0s.append(x)
            self.add_map_widget(widget)

    def add_map_widget(self, map_widget):
        self.stack.addWidget(map_widget)
        self.map_box.addItem(map_widget.name)


class MapWidget(QLabel, ClipableObserver, ImageObserver):
    def on_node_update(self, node):
        self.tex0 = node
        self.setToolTip(node.name)

    def on_child_update(self, child):
        pass

    def on_image_update(self, directory):
        update_image(self, directory, self.tex0.name, 128)

    def del_widget(self):
        self.tex0.unregister(self)
        ImageManager.get().unsubscribe(self, self.tex0.parent)
        self.setParent(None)

    def __init__(self, parent, tex0):
        self.name = tex0.name
        super().__init__(self.name, parent)
        tex0.register_observer(self)
        self.on_node_update(tex0)
        ImageManager.get().subscribe(self, tex0.parent)
        # if image_path:
        #     self.set_image_path(image_path)
