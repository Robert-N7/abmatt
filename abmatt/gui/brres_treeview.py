import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView, QMenu, QAction, QTreeWidgetItemIterator

# class BrresItemModel(QStandardItemModel):
#     def __init__(self):
from autofix import AutoFix
from brres.lib.node import ClipableObserver


class BrresTreeView(QTreeView):

    def __init__(self, parent):
        super().__init__(parent)
        self.handler = parent
        self.mdl = QStandardItemModel()
        self.setModel(self.mdl)
        self.clicked.connect(self.on_click)
        self.brres_map = {}
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_click)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    @staticmethod
    def __create_tree_item(linked_item, parent, use_base_name=False):
        item = QLinkedItem(linked_item, use_base_name)
        item.setEditable(False)
        parent.appendRow(item)
        return item

    def on_click(self, index):
        level, parent = self.get_indexed_level(index, get_parent=True)
        if level == 2:
            if self.handler is not None:
                self.handler.on_update_polygon(self.get_indexed_item(index))
        self.handler.set_brres(self.get_indexed_item(parent))

    @staticmethod
    def get_indexed_item(index):
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
        menu.addAction(imp)
        menu.addAction(exp)
        menu.addSeparator()
        menu.addAction(close)

    def import_file(self):
        self.handler.import_file_dialog(self.get_indexed_item(self.clicked_index))

    def export_file(self):
        self.handler.export_file_dialog()

    def close_file(self):
        self.handler.close_file(self.get_indexed_item(self.clicked_index))

    def start_context_menu(self, position, level):
        menu = QMenu()
        if level == 0:  # top level
            self.create_brres_menu(menu)
        elif level == 1:  # mdl0
            pass
        else:  # polygon
            pass
        menu.exec_(self.viewport().mapToGlobal(position))

    def on_context_click(self, position):
        indexes = self.selectedIndexes()
        if len(indexes) > 0:
            self.clicked_index = indexes[0]
            level = self.get_indexed_level(self.clicked_index)
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
                AutoFix.get().warn(f'{fname} has unknown extension')

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
            # i += 1

    def on_file_close(self, brres):
        """This is called when closing file"""
        # this needs to be changed if it's anything other than the clicked index
        try:
            item = self.brres_map.pop(brres.name)
            self.unlink_tree(item)
            self.mdl.removeRow(item.row(), self.clicked_index.parent())
        except KeyError:
            pass

    def on_brres_update(self, brres):
        """This provides a way to update brres tree (after conversion)"""
        self.on_file_close(brres)
        self.add_brres_tree(brres)


class QLinkedItem(QStandardItem, ClipableObserver):
    def __init__(self, linked_item, use_base_name=False):
        self.use_base_name = use_base_name
        self.name = linked_item.name if not use_base_name else os.path.basename(linked_item.name)
        super().__init__(self.name)
        self.linked_item = linked_item
        linked_item.register_observer(self)

    def on_rename_update(self, node):
        if self.use_base_name:
            name = os.path.basename(node.name)
        else:
            name = node.name
        if self.name != name:
            self.name = name
            self.setText(name)

    def unlink(self):
        self.linked_item.unregister(self)
