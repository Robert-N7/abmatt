import os
import sys

from PyQt5.QtGui import QStandardItemModel, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp, QFileDialog, QTreeView

from brres import Brres
from brres.lib.autofix import AUTO_FIXER
from converters.convert_dae import DaeConverter2
from converters.convert_obj import ObjConverter
from gui.brres_treeview import BrresTreeView
from load_config import load_config


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.open_files = []
        self.brres = None
        self.__init_UI()
        self.cwd = os.getcwd()
        AUTO_FIXER.set_pipe(self)
        self.show()

    def __init_menus(self):
        # Actions
        exit_act = QAction('&Exit', self)
        exit_act.setShortcut('Ctrl+q')
        exit_act.setStatusTip('Exit Application')
        exit_act.triggered.connect(self.quit)
        # Open
        open_act = QAction('&Open', self)
        open_act.setShortcut('Ctrl+o')
        open_act.setStatusTip('Open a Brres file')
        open_act.triggered.connect(self.open)
        # Save
        save_act = QAction('&Save', self)
        save_act.setShortcut('Ctrl+s')
        save_act.setStatusTip('Save file')
        save_act.triggered.connect(self.save)
        # Save as
        save_as = QAction('Save &As', self)
        save_as.setStatusTip('Save file as')
        save_as.triggered.connect(self.save_as)
        # import
        import_act = QAction('&Import', self)
        import_act.setShortcut('Ctrl+i')
        import_act.setStatusTip('Import file')
        import_act.triggered.connect(self.import_file)
        # export
        export_act = QAction('&Export', self)
        export_act.setShortcut('Ctrl+e')
        export_act.setStatusTip('Export file')
        export_act.triggered.connect(self.export_file)
        # File Menu
        menu = self.menuBar()
        fileMenu = menu.addMenu('&File')
        fileMenu.addAction(open_act)
        fileMenu.addAction(save_act)
        fileMenu.addAction(save_as)
        fileMenu.addSeparator()
        fileMenu.addAction(import_act)
        fileMenu.addAction(export_act)
        fileMenu.addSeparator()
        fileMenu.addAction(exit_act)

    def __init_UI(self):
        self.setWindowTitle('ANoobs Brres Material Tool')
        self.resize(800, 600)
        self.__init_menus()
        self.treeview = BrresTreeView(self)
        self.treeview.show()
        self.statusBar().showMessage('Ready')

    def set_brres(self, brres):
        self.brres = brres
        if brres not in self.open_files:
            self.open_files.append(brres)
            self.treeview.set_brres(brres)

    def open(self):
        fname, filter = QFileDialog.getOpenFileName(self, 'Open file',
                                            self.cwd, "Brres files (*.brres)")
        if fname:
            self.cwd = os.path.dirname(fname)
            self.set_brres(Brres(fname))

    def save(self):
        if self.brres is not None:
            self.brres.save()

    def save_as(self):
        fname, filter = QFileDialog.getSaveFileName(self, 'Save as', self.cwd, 'Brres files (*.brres)')
        if fname:
            self.cwd = os.path.dirname(fname)
            if self.brres:
                self.brres.save(fname, overwrite=True)

    def import_texture(self, filename):
        raise NotImplementedError()

    def import_file(self):
        fname, filter = QFileDialog.getOpenFileName(self, 'Import model', self.cwd, '(*.dae,*.obj)')
        if fname:
            self.cwd, name = os.path.split(fname)
            base_name, ext = os.path.splitext(name)
            lower = ext.lower()
            if lower == '.dae':
                converter = DaeConverter2(self.brres, fname)
                converter.load_model()
            elif lower == '.obj':
                converter = ObjConverter(self.brres, fname)
                converter.load_model()
            # elif lower in ('.png', '.jpg', '.bmp', '.tga'):
            #     return self.import_texture(fname)
            else:
                self.statusBar().showMessage('Unknown extension {}'.format(ext))

    def export_file(self):
        fname = QFileDialog.getSaveFileName(self, 'Export model', self.cwd, 'Model files (*.dae,*.obj)')
        if fname:
            self.cwd, name = os.path.split(fname)
            base_name, ext = os.path.splitext(name)
            lower = ext.lower()
            if ext == '.obj':
                converter = ObjConverter(self.brres, fname)
                converter.save_model()
            elif ext == '.dae':
                converter = DaeConverter2(self.brres, fname)
                converter.save_model()
            else:
                self.statusBar().showMessage('Unknown extension {}'.format(ext))

    def quit(self):
        for x in self.open_files:
            x.close()
        qApp.quit()

    def info(self, message):
        self.update_status(message)

    def warn(self, message):
        self.update_status(message)

    def error(self, message):
        self.update_status(message)

    def update_status(self, message):
        self.statusBar().showMessage(message)


def main(argv):
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = os.path.dirname(__file__)
    app_dir = os.path.join(os.path.join(os.path.dirname(os.path.dirname(base_path)), 'etc'), 'abmatt')
    load_config(app_dir)
    exe = QApplication(argv)
    d = Window()
    sys.exit(exe.exec_())


if __name__ == '__main__':
    main(sys.argv[1:])