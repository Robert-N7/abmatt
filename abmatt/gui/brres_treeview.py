import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView, QMenu, QAction, QInputDialog

from abmatt.autofix import AutoFix
from abmatt.brres.lib.node import ClipableObserver
from abmatt.gui.polygon_window import GLPolygonWidget


class BrresTreeView(QTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.handler = parent
        self.mdl = QStandardItemModel()
        self.setModel(self.mdl)
        self.clicked.connect(self.on_click)
        self.brres_map = {}
        self.named_items = {}
        self.clicked_index = None
        self.clicked_item = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_click)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def __create_tree_item(self, linked_item, parent, use_base_name=False):
        item = QLinkedItem(linked_item, use_base_name)
        item.setEditable(False)
        parent.appendRow(item)
        self.named_items[linked_item.name] = item
        return item

    def on_click(self, index):
        self.clicked_index = index
        self.clicked_item = self.get_indexed_item(index)
        level, parent = self.get_indexed_level(index, get_parent=True)
        if level == 2:
            if self.handler is not None:
                self.handler.on_update_polygon(self.clicked_item)
        self.handler.set_brres(self.get_indexed_item(parent))

    @staticmethod
    def get_indexed_item(index):
        if index is None:
            return None
        return index.model().itemFromIndex(index).linked_item

    @staticmethod
    def get_indexed_level(index, get_parent=False):
        level = 0
        while index.parent().isValid():
            index = index.parent()
            level += 1
        if get_parent:
            return level, index
        return level

    def __create_rename_action(self):
        action = QAction('&Rename', self)
        action.setStatusTip('Rename Node')
        action.triggered.connect(self.rename)
        return action

    def create_brres_menu(self, menu):
        imp = QAction('&Import', self)
        imp.setStatusTip('Import Model')
        imp.triggered.connect(self.import_file)
        exp = QAction('&Export', self)
        exp.setStatusTip('Export Model')
        exp.triggered.connect(self.export_file)
        close = QAction('&Close', self)
        close.setStatusTip('Close File')
        close.triggered.connect(self.close_file)
        menu.addAction(self.__create_rename_action())
        menu.addAction(imp)
        menu.addAction(exp)
        menu.addSeparator()
        menu.addAction(close)

    def create_mdl0_menu(self, menu):
        replace = QAction('Re&place', self)
        replace.setStatusTip('Replace Model')
        replace.triggered.connect(self.import_file)
        exp = QAction('&Export', self)
        exp.setStatusTip('Export Model')
        exp.triggered.connect(self.export_file)
        delete = QAction('&Delete', self)
        delete.setStatusTip('Delete Model')
        delete.triggered.connect(self.delete_node)
        menu.addAction(self.__create_rename_action())
        menu.addAction(replace)
        menu.addAction(exp)
        menu.addSeparator()
        menu.addAction(delete)

    def create_polygon_menu(self, menu):
        delete = QAction('&Delete', self)
        delete.setStatusTip('Delete Polygon')
        delete.triggered.connect(self.delete_node)
        view = QAction('&View', self)
        view.setStatusTip('View Polygon')
        view.triggered.connect(self.view_polygon)
        menu.addAction(view)
        menu.addAction(self.__create_rename_action())
        menu.addSeparator()
        menu.addAction(delete)

    def create_default_menu(self, menu):
        imp = QAction('&Import', self)
        imp.setStatusTip('Import Model')
        imp.triggered.connect(self.import_file)
        open = QAction('&Open', self)
        open.setStatusTip('Open Brres')
        open.triggered.connect(self.open_file)
        menu.addAction(open)
        menu.addAction(imp)

    def view_polygon(self):
        polygon = self.get_indexed_item(self.clicked_index)
        self.view_poly_win = GLPolygonWidget(polygon)
        self.view_poly_win.show()

    def rename(self):
        node = self.get_indexed_item(self.clicked_index)
        if self.level == 0:
            self.handler.save_as_dialog()
        elif self.level == 1:
            brres = node.parent
            old_name = node.name
            text, ok = QInputDialog.getText(self, 'Rename Node', 'Rename to:', text=old_name)
            if ok and text != old_name:
                if brres.get_model(text):
                    AutoFix.error('Model with name {} already exists!'.format(text))
                    return
                node.rename(text)
                self.handler.on_rename_update(node, old_name)
        elif self.level == 2:
            mdl0 = node.parent
            text, ok = QInputDialog.getText(self, 'Rename Node', 'Rename to:', text=node.name)
            if ok:
                if text in [x.name for x in mdl0.objects]:
                    AutoFix.error('Polygon with name {} already exists!'.format(text))
                    return
                node.rename(text)

    def delete_node(self):
        node = self.get_indexed_item(self.clicked_index)
        if self.level == 1:
            node.parent.remove_mdl0(node.name)
            self.on_brres_update(node.parent)
        elif self.level == 2:
            node.parent.remove_polygon(node)
            self.on_brres_update(node.parent.parent)

    def open_file(self):
        self.handler.open_dialog()

    def import_file(self):
        if self.level > 0:
            self.handler.import_file_dialog(mdl0=self.get_indexed_item(self.clicked_index))
        else:
            self.handler.import_file_dialog(self.get_indexed_item(self.clicked_index))

    def export_file(self):
        if self.level > 0:
            self.handler.export_file_dialog(mdl0=self.get_indexed_item(self.clicked_index))
        else:
            self.handler.export_file_dialog(self.get_indexed_item(self.clicked_index))

    def close_file(self):
        self.handler.close_file(self.get_indexed_item(self.clicked_index))

    def start_context_menu(self, position, level):
        menu = QMenu()
        if level == -1:
            self.create_default_menu(menu)
        elif level == 0:  # top level
            self.create_brres_menu(menu)
        elif level == 1:  # mdl0
            self.create_mdl0_menu(menu)
        else:  # polygon
            self.create_polygon_menu(menu)
        menu.exec_(self.viewport().mapToGlobal(position))

    def on_context_click(self, position):
        indexes = self.selectedIndexes()
        if len(indexes) > 0:
            self.clicked_index = indexes[0]
            self.clicked_item = self.get_indexed_item(self.clicked_index)
            level = self.get_indexed_level(self.clicked_index)
        else:
            self.clicked_index = None
            level = -1
        self.level = level
        self.start_context_menu(position, level)

    def dragEnterEvent(self, event):
        m = event.mimeData()
        if m.hasUrls() and self.check_urls(event.mimeData().urls()):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and self.check_urls(event.mimeData().urls()):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        m = event.mimeData()
        if m.hasUrls():
            strings = self.check_urls(m.urls())
            if strings:
                event.accept()
                self.add_files(strings)
        else:
            event.ignore()

    def check_urls(self, urls):
        strings = [str(url.toLocalFile()) for url in urls]
        if self.check_ext(strings):
            return strings

    def check_ext(self, files):
        valid_exts = ('.dae', '.obj', '.brres')
        for file in files:
            if os.path.splitext(os.path.basename(file))[1].lower() not in valid_exts:
                return False
        return True

    def add_files(self, files):
        for fname in files:
            dir, name = os.path.split(fname)
            ext = os.path.splitext(name)[1].lower()
            if ext in ('.dae', '.obj'):
                self.handler.import_file(fname)
            elif ext == '.brres':
                self.handler.open(fname)
            # elif ext in ('.png', '.jpg', '.bmp', '.tga'):
            #     self.handler.import_texture(fname)
            else:
                AutoFix.warn(f'{fname} has unknown extension')

    def add_mdl0_item(self, brres_tree, mdl0):
        mdl0_tree = self.__create_tree_item(mdl0, brres_tree)
        for polygon in mdl0.objects:
            self.__create_tree_item(polygon, mdl0_tree)

    def add_brres_tree(self, brres):
        self.brres_map[brres.name] = brres_tree = self.__create_tree_item(brres, self.mdl, use_base_name=True)
        for model in brres.models:
            self.add_mdl0_item(brres_tree, model)

    def unlink_tree(self, item):
        """Unlinks the tree"""
        # couldn't seem to find any iterators like this so here we go
        i = 0
        item.unlink()
        while True:
            x = item.takeChild(i)
            if x is None:
                return
            self.unlink_tree(x)

    def on_file_close(self, brres):
        """This is called when closing file"""
        # this needs to be changed if it's anything other than the clicked index
        try:
            item = self.brres_map.pop(brres.name)
            if item:
                self.unlink_tree(item)
                self.mdl.removeRow(item.row())
        except KeyError:
            pass

    def on_brres_rename(self, old_name, new_name):
        item = self.brres_map.get(old_name)
        if item is not None:
            self.brres_map[new_name] = item
            self.brres_map[old_name] = None

    def expand_parents(self, index):
        self.setExpanded(index, True)
        parent = index.parent()
        if parent.isValid():
            self.expand_parents(parent)

    def on_brres_update(self, brres):
        """This provides a way to update brres tree (after conversion)"""
        self.on_file_close(brres)
        self.add_brres_tree(brres)
        if self.clicked_item:
            index = self.model().indexFromItem(self.named_items[self.clicked_item.name])
            self.expand_parents(index)


class QLinkedItem(QStandardItem, ClipableObserver):
    def __init__(self, linked_item, use_base_name=False):
        self.use_base_name = use_base_name
        self.name = linked_item.name if not use_base_name else os.path.basename(linked_item.name)
        super().__init__(self.name)
        self.linked_item = linked_item
        linked_item.register_observer(self)

    def __del__(self):
        if self.linked_item is not None:
            self.linked_item.unregister(self)

    def on_rename_update(self, node, old_name):
        if self.use_base_name:
            name = os.path.basename(node.name)
        else:
            name = node.name
        if self.name != name:
            self.name = name
            self.setText(name)

    def unlink(self):
        self.linked_item.unregister(self)
        self.linked_item = None
