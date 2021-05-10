import os
import platform
import sys
import traceback
import webbrowser

from PyQt5.QtCore import QThreadPool
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QFileDialog, QVBoxLayout, QHBoxLayout, \
    QWidget, QPlainTextEdit, QMessageBox, QSizePolicy

from abmatt.autofix import AutoFix
from abmatt.brres.brres import Brres
from abmatt.brres.lib.node import ClipableObserver
from abmatt.command import Command
from abmatt.converters.convert_dae import DaeConverter
from abmatt.converters.convert_obj import ObjConverter
from abmatt.gui.brres_treeview import BrresTreeView
from abmatt.gui.converter import ConvertManager
from abmatt.gui.image_manager import ImageManager
from abmatt.gui.interactive_cmd import InteractiveCmd
from abmatt.gui.kcl_calculator import KCLCalculator
from abmatt.gui.logger_pipe import LoggerPipe
from abmatt.gui.material_browser import MaterialTabs
from abmatt.gui.poly_editor import PolyEditor
from abmatt import load_config


class Window(QMainWindow, ClipableObserver):

    def __init__(self, brres_files=[]):
        super().__init__()
        self.open_files = []
        self.brres = None
        self.image_updater = {}     # maps brres to list of subscribers
        self.cwd = os.getcwd()
        self.__init_threads()
        self.locked_files = set()       # lock files that are pending conversion etc...
        # AutoFix.set_pipe(self)
        self.__init_UI()
        self.shell_is_shown = False
        self.shell = None
        for file in brres_files:
            self.open(file.name)
        AutoFix.info('Initialized main window', 5)
        self.show()

    def __init_threads(self):
        AutoFix.info('Starting threads...', 5)
        self.threadpool = QThreadPool()     # for multi-threading
        self.threadpool.setMaxThreadCount(5)
        self.converter = converter = ConvertManager.get()
        converter.signals.on_conversion_finish.connect(self.on_conversion_finish)
        self.image_manager = image_manager = ImageManager.get()
        if image_manager.enabled:
            image_manager.signals.on_image_update.connect(self.on_image_update)
            self.threadpool.start(image_manager)
        else:
            AutoFix.warn('Image Manager disabled, do you have Wiimms SZS Tools installed?')
        self.threadpool.start(converter)
        log_pipe = LoggerPipe()
        log_pipe.info_sig.connect(self.info)
        log_pipe.warn_sig.connect(self.warn)
        log_pipe.error_sig.connect(self.error)

    def __init_menus(self):
        # Files
        # Exit
        exit_act = QAction('&Exit', self)
        exit_act.setShortcut('Ctrl+q')
        exit_act.setStatusTip('Exit Application')
        exit_act.triggered.connect(self.close)
        # Open
        open_act = QAction('&Open', self)
        open_act.setShortcut('Ctrl+o')
        open_act.setStatusTip('Open a Brres file')
        open_act.triggered.connect(self.open_dialog)
        # Save
        save_act = QAction('&Save', self)
        save_act.setShortcut('Ctrl+s')
        save_act.setStatusTip('Save file')
        save_act.triggered.connect(self.save)
        # Save as
        save_as = QAction('Save &As', self)
        save_as.setStatusTip('Save file as')
        save_as.triggered.connect(self.save_as_dialog)
        # import
        import_act = QAction('&Import', self)
        import_act.setShortcut('Ctrl+i')
        import_act.setStatusTip('Import file')
        import_act.triggered.connect(self.import_file_dialog)
        # export
        export_act = QAction('&Export', self)
        export_act.setShortcut('Ctrl+e')
        export_act.setStatusTip('Export file')
        export_act.triggered.connect(self.export_file_dialog)
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

        # Tools
        shell_Act = QAction('&Interactive Shell', self)
        shell_Act.setShortcut('Ctrl+Shift+I')
        shell_Act.setStatusTip('Run interactive commands')
        shell_Act.triggered.connect(self.open_interactive_shell)
        kcl_calc_Act = QAction('&KCL Calculator', self)
        kcl_calc_Act.setShortcut('Ctrl+k')
        kcl_calc_Act.setStatusTip('KCL Flag Calculator')
        kcl_calc_Act.triggered.connect(self.open_kcl_calculator)
        toolMenu = menu.addMenu('&Tools')
        toolMenu.addAction(shell_Act)
        toolMenu.addAction(kcl_calc_Act)

        # Help
        report_Act = QAction('&Report Issue', self)
        report_Act.setStatusTip('Report an issue')
        report_Act.triggered.connect(self.report_issue)
        website_Act = QAction('&Website', self)
        website_Act.setStatusTip('Visit website')
        website_Act.triggered.connect(self.open_website)
        about_Act = QAction('&About', self)
        about_Act.setStatusTip('Information about ABMatt')
        about_Act.triggered.connect(self.about_abmatt)
        help_menu = menu.addMenu('&Help')
        help_menu.addAction(report_Act)
        help_menu.addAction(website_Act)
        help_menu.addSeparator()
        help_menu.addAction(about_Act)

    def open_website(self):
        webbrowser.open('https://github.com/Robert-N7/abmatt')

    def report_issue(self):
        webbrowser.open('https://github.com/Robert-N7/abmatt/issues')

    def about_abmatt(self):
        self.box = QMessageBox()
        bit_size = '64-Bit' if sys.maxsize > 2 ** 32 else '32-Bit'
        self.box.setText(f'ABMatt Version {load_config.VERSION} {platform.platform()} {bit_size}')
        self.box.setWindowTitle('ABMatt')
        self.box.show()

    def open_kcl_calculator(self):
        self.calculator = KCLCalculator()

    def open_interactive_shell(self):
        if not self.shell_is_shown:
            if self.shell is None:
                self.shell = InteractiveCmd()
                self.left.addWidget(self.shell)
            else:
                self.shell.show()
            self.shell_is_shown = True
        else:
            self.shell_is_shown = False
            self.shell.hide()

    def locate_material(self, brres_path):
        return self.material_browser.locate_material(brres_path)

    def __init_child_UI(self, top_layout):
        # left
        vert_widget = QWidget(self)
        # policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        # policy.setHorizontalStretch(2)
        # vert_widget.setSizePolicy(policy)
        top_layout.addWidget(vert_widget)
        self.left = vert_layout = QVBoxLayout()
        vert_widget.setLayout(vert_layout)
        widget = QWidget(self)
        vert_layout.addWidget(widget)
        center_layout = QHBoxLayout()
        widget.setLayout(center_layout)
        self.logger = QPlainTextEdit(self)
        self.logger.setReadOnly(True)
        self.logger.setFixedHeight(100)
        vert_layout.addWidget(self.logger)

        self.treeview = BrresTreeView(self)
        self.treeview.setMinimumWidth(300)
        center_layout.addWidget(self.treeview)
        self.poly_editor = PolyEditor(self)
        center_layout.addWidget(self.poly_editor)
        # center_widget.setGeometry(0, 0, 300, 300)

        # right
        # top_layout.addSpacing(30)
        self.material_browser = MaterialTabs(self)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        policy.setHorizontalStretch(1)
        self.material_browser.setSizePolicy(policy)
        top_layout.addWidget(self.material_browser)
        # self.material_browser.setFixedWidth(300)

    def __init_UI(self):
        self.setWindowTitle('ANoobs Brres Material Tool')
        self.resize(1000, 700)
        self.__init_menus()
        main_layout = QHBoxLayout()
        self.__init_child_UI(main_layout)
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        self.statusBar().showMessage('Ready')

    def on_image_update(self, brres_dir):
        # simply gives it back to the image manager to update observers
        self.image_manager.notify_image_observers(*brres_dir)

    def on_update_polygon(self, poly):
        enable_edits = poly.parent.parent not in self.locked_files
        self.poly_editor.on_update_polygon(poly, enable_edits=enable_edits)

    def emit(self, message, head=None, tail=None):
        message = message.replace('\n', '<br/>').replace(' ', '&nbsp;')
        if head:
            message = head + message
        if tail:
            message += tail
        self.logger.appendHtml(message)

    def get_brres_by_fname(self, fname):
        path = os.path.abspath(fname)
        for x in self.open_files:
            if os.path.abspath(x.name) == path:
                return x

    def set_brres(self, brres):
        if brres != self.brres:
            self.brres = brres

    def open_dialog(self):
        fname, filter = QFileDialog.getOpenFileName(self, 'Open file',
                                                    self.cwd, "Brres files (*.brres)")
        if fname:
            self.open(fname)

    def on_node_update(self, node):
        self.treeview.on_brres_update(node)

    def on_rename_update(self, node, old_name):
        if type(node) == Brres:
            self.treeview.on_brres_rename(old_name, node.name)
        self.material_browser.on_name_update()

    def on_child_update(self, child):
        self.treeview.on_brres_update(child.parent)

    def open(self, fname, force_update=False):
        self.cwd = os.path.dirname(fname)
        opened = self.get_brres_by_fname(fname)
        if opened:
            if not force_update:
                return self.set_brres(opened)
        else:
            opened = Brres.get_brres(fname)
            self.open_files.append(opened)
            opened.register_observer(self)
        # either it's newly opened or forcing update
        self.set_brres(opened)
        self.treeview.on_brres_update(opened)
        self.material_browser.add_brres_materials_to_scene(opened)

    def save(self):
        if len(self.open_files):
            last = None
            for x in self.open_files:
                # A precaution against overwriting old models
                # overwrite = True if not x.has_new_model else Brres.OVERWRITE
                if x.save(overwrite=True):
                    last = x
            if last is not None:
                self.update_status('Wrote file {}'.format(last.name))

    def save_as_dialog(self):
        if self.brres:
            fname, filter = QFileDialog.getSaveFileName(self, 'Save as', self.cwd, 'Brres files (*.brres)')
            if fname:
                self.cwd = os.path.dirname(fname)
                self.brres.save(fname, overwrite=True)
                self.update_status('Wrote file {}'.format(fname))
        else:
            AutoFix.error('No Brres file selected.')

    def import_texture(self, filename):
        raise NotImplementedError()

    def on_material_select(self, material):
        self.material_browser.on_material_select(material)

    def import_file(self, fname, brres_name=None, brres=None, mdl0=None):
        if mdl0 is not None:
            brres = mdl0.parent
        if not brres:
            if brres_name is not None:
                brres = self.get_brres_by_fname(brres_name)
            elif self.brres and os.path.splitext(os.path.basename(self.brres.name))[0] == \
                    os.path.splitext(os.path.basename(fname))[0]:
                brres = self.brres
        self.cwd, name = os.path.split(fname)
        base_name, ext = os.path.splitext(name)
        lower = ext.lower()
        if lower == '.dae':
            converter = DaeConverter(brres, fname, mdl0=mdl0)
        elif lower == '.obj':
            converter = ObjConverter(brres, fname, mdl0=mdl0)
        # elif lower in ('.png', '.jpg', '.bmp', '.tga'):
        #     return self.import_texture(fname)
        else:
            self.statusBar().showMessage('Unknown extension {}'.format(ext))
            return
        # converter.load_model()
        # self.on_conversion_finish(converter)
        self.update_status('Added {} to queue...'.format(fname))
        self.lock_file(converter.brres)
        self.converter.enqueue(converter)

    def lock_file(self, brres):
        self.locked_files.add(brres)
        self.poly_editor.on_brres_lock(brres)

    def unlock_file(self, brres):
        try:
            self.locked_files.remove(brres)
        except KeyError:
            pass
        self.poly_editor.on_brres_unlock(brres)

    def on_conversion_finish(self, converter):
        self.open(converter.brres.name, force_update=True)
        self.unlock_file(converter.brres)
        self.update_status('Finished Converting {}'.format(converter.brres.name))

    def import_file_dialog(self, brres=None, mdl0=None):
        fname, filter = QFileDialog.getOpenFileName(self, 'Import model', self.cwd, '(*.dae *.obj)')
        if fname:
            self.import_file(fname, brres=brres, mdl0=mdl0)

    def export_file_dialog(self, brres=None, mdl0=None):
        if mdl0 is not None:
            brres = mdl0.parent
        multiple_models = False
        if not brres:
            brres = self.brres
            if not brres:
                AutoFix.error('Nothing to export!')
                return
        elif mdl0 is None:
            if len(brres.models) > 1:
                multiple_models = True
        fname, fil = QFileDialog.getSaveFileName(self, 'Export model', self.cwd, 'Model files (*.dae *.obj)')
        if fname:
            self.cwd, name = os.path.split(fname)
            base_name, ext = os.path.splitext(name)
            lower = ext.lower()
            if lower == '.obj':
                klass = ObjConverter
            elif lower == '.dae':
                klass = DaeConverter
            else:
                self.statusBar().showMessage('Unknown extension {}'.format(ext))
                return
            if multiple_models:
                for x in brres.models:
                    export_name = os.path.join(self.cwd, base_name + '-' + x.name + ext)
                    converter = klass(brres, export_name, encode=False, mdl0=x)
                    self.update_status('Added {} to queue...'.format(x.name))
                    self.converter.enqueue(converter)
            else:
                if mdl0 is None:
                    mdl0 = brres.models[0]
                converter = klass(brres, fname, encode=False, mdl0=mdl0)
                self.update_status('Added {} to queue...'.format(mdl0.name))
                self.converter.enqueue(converter)

    def close_file(self, brres=None):
        if brres is None:
            brres = self.brres
        if brres.is_modified:
            m = QMessageBox(QMessageBox.Warning, 'Save Before Closing',
                            f'Save {brres.name} before closing?',
                            buttons=QMessageBox.Yes | QMessageBox.No, parent=self)
            if m.exec_() == QMessageBox.Yes:
                brres.save(overwrite=True)
        if brres in self.open_files:
            self.open_files.remove(brres)
            brres.unregister(self)
        brres.close(try_save=False)
        self.brres = None
        self.poly_editor.on_brres_lock(brres)
        self.treeview.on_file_close(brres)

    def shouldExitAnyway(self, result):
        return result == QMessageBox.Ok

    def closeEvent(self, event):
        self.material_browser.on_close()
        files_to_save = []
        for x in self.open_files:
            if x.is_modified:
                files_to_save.append(x)
        if Brres.OVERWRITE:
            for x in files_to_save:
                x.close()
        elif files_to_save:
            self.files_to_save = files_to_save
            fnames = ', '.join([x.name for x in files_to_save])

            m = QMessageBox(QMessageBox.Warning, 'Confirm Exit?',
                            f'Exit without saving {fnames}?', buttons=QMessageBox.Yes | QMessageBox.No, parent=self)

            if m.exec_() == QMessageBox.No:
                event.ignore()
                return
            for x in files_to_save:
                x.close()
        self.threadpool.clear()
        self.image_manager.stop()
        self.converter.stop()
        event.accept()

    def info(self, message):
        self.emit(message, '<p style="color:Blue;">', '</p>')

    def warn(self, message):
        self.emit(message, '<p style="color:Red;">', '</p>')

    def error(self, message):
        self.emit(message, '<p style="color:Red;">', '</p>')

    def update_status(self, message):
        self.statusBar().showMessage(message)


def on_exit():
    #   join other threads
    AutoFix.quit()


def main():
    argv = sys.argv[1:]
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    load_config.parse_args(argv, base_path)
    exe = QApplication(argv)
    exe.setStyle('Fusion')
    exe.setWindowIcon(QIcon(os.path.join(Command.APP_DIR, 'icon.ico')))
    d = Window()
    result = exe.exec_()
    on_exit()
    if result:
        sys.exit(result)


# sys._excepthook = sys.excepthook
#
# def my_exception_hook(exctype, value, traceback):
#     # Print the error and traceback
#     print(exctype, value, traceback)
#     # Call the normal Exception hook after
#     sys._excepthook(exctype, value, traceback)
#     sys.exit(1)
#
# sys.excepthook = my_exception_hook

if __name__ == '__main__':
    try:
        main()
    except:
        traceback.print_exc()

