from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView, QMenu

# class BrresItemModel(QStandardItemModel):
#     def __init__(self):


class BrresTreeView(QTreeView):

    def __init__(self, parent, poly_updater=None):
        super().__init__(parent)
        self.mdl = QStandardItemModel()
        self.setModel(self.mdl)
        self.setGeometry(10, 30, 300, 400)
        self.clicked.connect(self.on_click)
        self.poly_updater = poly_updater
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.on_context_click)
        # self.setDragEnabled(True)
        # self.setAcceptDrops(True)
        # self.setDropIndicatorShown(True)

    @staticmethod
    def __create_tree_item(linked_item, parent):
        item = QLinkedItem(linked_item)
        item.setEditable(False)
        parent.appendRow(item)
        return item

    def on_click(self, index):
        if self.get_indexed_level(index) == 2:
            if self.poly_updater is not None:
                poly = index.model().itemFromIndex(index).linked_item
                self.poly_updater.on_update_polygon(poly)

    def get_indexed_level(self, index):
        level = 0
        while index.parent().isValid():
            index = index.parent()
            level += 1
        return level

    # def on_context_click(self, position):
    #     indexes = self.selectedIndexes()
    #     if len(indexes) > 0:
    #         level = 0
    #         index = indexes[0]
    #         while index.parent().isValid():
    #             index = index.parent()
    #             level += 1
    #     else:
    #         return
        # menu = QMenu()
        # menu.exec_(self.viewport().mapToGlobal(position))

    # def dragEnterEvent(self, event):
    #     m = event.mimeData()
    #     if m.hasUrls():
    #         for url in m.urls():
    #             if url.isLocalFile():
    #                 event.accept()
    #                 return
    #     event.ignore()

    def dropEvent(self, event):
        if event.source():
            QTreeView.dropEvent(self, event)
        else:
            ix = self.indexAt(event.pos())
            if not self.model().isDir(ix):
                ix = ix.parent()
            pathDir = self.model().filePath(ix)
            m = event.mimeData()
            if m.hasUrls():
                urlLocals = [url for url in m.urls() if url.isLocalFile()]
                accepted = False
                for urlLocal in urlLocals:
                    path = urlLocal.toLocalFile()
                    # info = QFileInfo(path)
                    # n_path = QDir(pathDir).filePath(info.fileName())
                    # o_path = info.absoluteFilePath()
                    # if n_path == o_path:
                    #     continue
                    # if info.isDir():
                    #     QDir().rename(o_path, n_path)
                    # else:
                    #     qfile = QFile(o_path)
                    #     if QFile(n_path).exists():
                    #         n_path += "(copy)"
                    #     qfile.rename(n_path)
                    accepted = True
                if accepted:
                    event.acceptProposedAction()

    def add_mdl0_item(self, brres_tree, mdl0):
        mdl0_tree = self.__create_tree_item(mdl0, brres_tree)
        # polys
        # poly_tree = self.__create_tree_item('Polygons', mdl0_tree)
        for polygon in mdl0.objects:
            self.__create_tree_item(polygon, mdl0_tree)
        # mats
        # mat_tree = self.__create_tree_item('Materials', mdl0_tree)
        # for mat in mdl0.materials:
        #     self.__create_tree_item(mat.name, mat_tree)

    def add_brres_tree(self, brres):
        brres_tree = self.__create_tree_item(brres, self.mdl)
        for model in brres.models:
            self.add_mdl0_item(brres_tree, model)


class QLinkedItem(QStandardItem):
    def __init__(self, linked_item):
        super().__init__(linked_item.name)
        self.linked_item = linked_item
