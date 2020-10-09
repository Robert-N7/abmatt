from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QTreeView, QMenu

# class BrresItemModel(QStandardItemModel):
#     def __init__(self):


class BrresTreeView(QTreeView):

    def __init__(self, parent):
        super().__init__(parent)
        self.mdl = QStandardItemModel()
        self.setModel(self.mdl)
        self.setGeometry(10, 30, 300, 400)
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.on_context_click)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    @staticmethod
    def __create_tree_item(name, parent):
        item = QStandardItem(name)
        item.setEditable(False)
        parent.appendRow(item)
        return item

    def on_context_click(self, position):
        indexes = self.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        menu = QMenu()
        # if level == 0:
        menu.exec_(self.viewport().mapToGlobal(position))

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
        mdl0_tree = self.__create_tree_item(mdl0.name, brres_tree)
        # polys
        poly_tree = self.__create_tree_item('Polygons', mdl0_tree)
        for polygon in mdl0.objects:
            self.__create_tree_item(polygon.name, poly_tree)
        # mats
        mat_tree = self.__create_tree_item('Materials', mdl0_tree)
        for mat in mdl0.materials:
            self.__create_tree_item(mat.name, mat_tree)

    def set_brres(self, brres):
        brres_tree = self.__create_tree_item(brres.name, self.mdl)
        for model in brres.models:
            self.add_mdl0_item(brres_tree, model)
