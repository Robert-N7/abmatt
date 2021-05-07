import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedLayout, QComboBox, QLabel, QGridLayout, QLineEdit, \
    QSpinBox, QHBoxLayout, QPushButton, QFileDialog, QAction

from abmatt.autofix import AutoFix
from abmatt.brres.lib.node import ClipableObserver
from abmatt.brres.tex0 import Tex0
from abmatt.gui.image_manager import ImageObserver, update_image, ImageManager
from abmatt.image_converter import ImgConverter, EncodeError


def is_image_url(path):
    ext = os.path.splitext(os.path.basename(path))[1]
    return ext == '.jpg' or ext == '.png' or ext == '.bmp' or ext == '.tpl'


class Tex0WidgetSubscriber:
    def on_map_change(self, tex0, index):
        raise NotImplementedError()

    def on_map_add(self, tex0, index):
        raise NotImplementedError()

    def on_map_remove(self, tex0, index):
        raise NotImplementedError()

    def on_map_replace(self, tex0, index):
        raise NotImplementedError()


class Tex0WidgetGroup(QWidget):
    def __init__(self, parent, tex0s=None, max_rows=0, max_columns=4, brres=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        self.stack = QStackedLayout(self)
        self.stack_widget = QWidget(self)
        self.map_box = QComboBox()
        self.map_box.activated.connect(self.on_map_change)
        self.__init_context_menu()
        main_layout.addWidget(self.map_box)
        self.stack_widget.setLayout(self.stack)
        main_layout.addWidget(self.stack_widget)
        self.subscriber = parent
        if tex0s is not None:
            self.set_tex0s(tex0s)
            if brres is None:
                self.brres = tex0s[0].parent
        if brres:
            self.brres = brres
        self.setLayout(main_layout)

    def __init_context_menu(self):
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        create_action = QAction('&Add Map', self)
        create_action.setToolTip('Add new map')
        create_action.triggered.connect(self.create_map)
        self.addAction(create_action)
        replace_action = QAction('&Replace', self)
        replace_action.setToolTip('Replace map')
        replace_action.triggered.connect(self.replace_map)
        self.addAction(replace_action)
        export_action = QAction('&Export', self)
        export_action.setToolTip('Export as png')
        export_action.triggered.connect(self.export)
        self.addAction(export_action)
        remove_action = QAction('&Delete', self)
        remove_action.setToolTip('Remove the map')
        remove_action.triggered.connect(self.remove)
        self.addAction(remove_action)

    def export(self):
        self.stack.currentWidget().export()

    def remove(self):
        self.remove_map_widget(self.stack.currentWidget())

    def replace_map(self):
        self.stack.currentWidget().replace_map()

    def get_tex0(self, index):
        return self.stack.itemAt(index).tex0

    def on_map_replace(self, tex):
        if self.subscriber is not None:
            self.subscriber.on_map_replace(tex, self.stack.currentIndex())

    def on_map_change(self, index):
        self.stack.setCurrentIndex(index)
        if self.subscriber is not None:
            self.subscriber.on_map_change(self.stack.currentWidget().tex0, index)

    def reset(self):
        for i in reversed(range(self.stack.count())):
            widget = self.stack.itemAt(i).widget()
            widget.del_widget()
            self.map_box.removeItem(i)

    def set_brres(self, brres):
        self.brres = brres

    def set_tex0s(self, tex0s):
        self.reset()
        for x in tex0s:
            self.add_tex0(x)

    def add_tex0(self, x):
        widget = MapWidget(self, x)
        self.add_map_widget(widget)

    def add_map_widget(self, map_widget):
        self.stack.addWidget(map_widget)
        self.map_box.addItem(map_widget.name)

    def remove_map_widget(self, map_widget):
        tex0 = map_widget.tex0
        index = self.stack.currentIndex()
        if self.subscriber is not None:
            self.subscriber.on_map_remove(tex0, index)

    def create_map(self):
        self.importer = MapImporter(self, self.brres)

    def on_import(self, tex0):
        index = self.stack.count()
        if self.subscriber:
            self.subscriber.on_map_add(tex0, index)
        self.importer = None


def dragTest(ev):
    data = ev.mimeData()
    if data.hasUrls():
        if len(data.urls()) != 1:
            success = False
        else:
            success = True
            for url in data.urls():
                if not is_image_url(url.toLocalFile()):
                    success = False
                    break
    else:
        success = False
    if success:
        ev.accept()
    else:
        ev.ignore()
    return success


class MapWidget(QLabel, ClipableObserver, ImageObserver):
    def on_node_update(self, node):
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
        self.handler = parent
        super().__init__(self.name, parent)
        self.tex0 = None
        self.set_tex0(tex0)
        self.setAcceptDrops(True)
        ImageManager.get().subscribe(self, tex0.parent)
        # if image_path:
        #     self.set_image_path(image_path)

    def export(self):
        self.exporter = MapExporter(self.tex0)
        self.exporter.show()

    def set_tex0(self, tex0):
        replaced = False
        if self.tex0 is not None:
            self.tex0.unregister(self)
            replaced = True
        self.tex0 = tex0
        tex0.register_observer(self)
        self.on_node_update(tex0)
        if replaced:
            self.handler.on_map_replace(tex0)

    def on_import(self, tex0):
        self.set_tex0(tex0)
        self.importer = None

    def dragEnterEvent(self, ev):
        dragTest(ev)

    def dragMoveEvent(self, ev):
        dragTest(ev)

    def replace_map(self, path=None):
        self.importer = MapImporter(self, self.tex0.parent, path=path)

    def dropEvent(self, ev):
        if dragTest(ev):
            self.replace_map(ev.mimeData().urls()[0].toLocalFile())


class MapImporter(QWidget):
    def __init__(self, import_handler, brres, path=None):
        super().__init__()
        self.import_handler = import_handler
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Map Importer')
        self.__init_ui()
        self.brres = brres
        if path:
            self.set_path(path)
        self.setAcceptDrops(True)
        self.show()

    def dragEnterEvent(self, ev):
        dragTest(ev)

    def dragLeaveEvent(self, ev):
        dragTest(ev)

    def dropEvent(self, ev):
        if dragTest(ev):
            self.set_path(ev.mimeData().urls()[0].toLocalFile())

    def __start_row(self):
        layout = QHBoxLayout(self)
        widget = QWidget(self)
        widget.setLayout(layout)
        self.main_layout.addWidget(widget)
        return layout

    def set_path(self, path):
        self.path_edit.setText(path)

    def __init_ui(self):
        self.main_layout = QVBoxLayout()
        layout = self.__start_row()
        file_lbl = QLabel('File', self)
        self.path_edit = QLineEdit(self)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse)
        layout.addWidget(file_lbl)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        layout = self.__start_row()
        format_lbl = QLabel('Format')
        self.format_box = QComboBox(self)
        self.format_box.addItems(Tex0.FORMATS.values())
        self.format_box.setCurrentIndex(10)
        num_mips_lbl = QLabel('Mipmaps (-1 = auto)')
        self.num_mips = QSpinBox(self)
        self.num_mips.setMinimum(-1)
        self.num_mips.setMaximum(8)
        self.num_mips.setValue(-1)
        layout.addWidget(format_lbl)
        layout.addWidget(self.format_box)
        layout.addWidget(num_mips_lbl)
        layout.addWidget(self.num_mips)
        # self.preview = QLabel(self)
        # self.main_layout.addWidget(self.preview)
        layout = self.__start_row()
        self.cancel_button = QPushButton('&Cancel', self)
        self.cancel_button.clicked.connect(self.cancel)
        self.import_button = QPushButton('&Import', self)
        self.import_button.clicked.connect(self.import_map)
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.import_button)
        self.setLayout(self.main_layout)

    def browse(self):
        fileName = QFileDialog.getOpenFileName(self, "Open Image", os.getcwd(), "Image Files (*.png *.jpg *.bmp)")[0]
        if fileName:
            self.set_path(fileName)

    def cancel(self):
        self.close()

    def import_map(self):
        fmt = self.format_box.currentText()
        mips = self.num_mips.value()
        path = self.path_edit.text()
        try:
            tex0 = ImgConverter().INSTANCE.encode(path, self.brres, tex_format=fmt, num_mips=mips)
            if not tex0:
                tex0 = self.brres.get_texture(os.path.splitext(os.path.basename(path))[0])
            self.import_handler.on_import(tex0)
        except EncodeError as e:
            AutoFix.error(e)
        self.close()


class MapExporter(QWidget):
    def __init__(self, tex0, parent=None, path=None):
        super().__init__(parent)
        self.tex0 = tex0
        self.handler = parent
        self.__init_ui(path)
        self.setWindowTitle('Map Exporter')
        self.show()

    def __init_ui(self, path):
        layout = QGridLayout()
        self.tex0_label = QLabel('Exporting ' + self.tex0.name + '...')
        layout.addWidget(self.tex0_label)
        # self.name = QLabel(self.tex0.name, self)
        # layout.addWidget(self.name, 0, 1)
        self.path_edit = QLineEdit(self)
        self.path_edit.setMinimumWidth(300)
        if path is not None:
            self.path_edit.setText(path)
        layout.addWidget(self.path_edit)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse)
        layout.addWidget(self.browse_button, 1, 1)
        self.mipmap_label = QLabel('Mipmaps (-1=auto)', self)
        layout.addWidget(self.mipmap_label)
        self.mipmap_count = QSpinBox(self)
        self.mipmap_count.setMinimum(-1)
        self.mipmap_count.setMaximum(10)
        self.mipmap_count.setValue(0)
        layout.addWidget(self.mipmap_count, 2, 1)
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel)
        self.submit = QPushButton('Submit')
        self.submit.clicked.connect(self.on_submit)
        layout.addWidget(self.submit, 3, 1)
        self.setLayout(layout)

    def on_submit(self):
        path = self.path_edit.text()
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            AutoFix.error('Path {} does not exist!'.format(path))
        else:
            ImgConverter().decode(self.tex0, path, overwrite=True, num_mips=self.mipmap_count.value())
            AutoFix.info('Exported {} to {}'.format(self.tex0.name, path))
            self.close()

    def on_cancel(self):
        self.close()

    def browse(self):
        fname = QFileDialog.getSaveFileName(self, 'Save Image', os.getcwd(), "Image Files (*.png)")[0]
        if fname:
            self.path_edit.setText(fname)
