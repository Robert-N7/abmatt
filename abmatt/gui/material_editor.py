from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


class MaterialEditor(QWindow):
    def __init__(self, parent, material):
        self.material = material
        self.init_UI()
        super().__init__(parent)

    def init_UI(self):
        pass