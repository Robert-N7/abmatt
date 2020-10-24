from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QTextEdit, QLineEdit

from abmatt.autofix import AutoFix
from abmatt.command import Command, ParsingException


class InteractiveCmd(QLineEdit):
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)
        self.setPlaceholderText('Enter command here...')
        self.cmds_run = []
        self.cmd_index = 0
        self.setFocus()

    def try_parse(self, text):
        try:
            self.cmds_run.append(text)
            if len(self.cmds_run) > 10:
                self.cmds_run.pop(0)
            return Command.run_commands([Command(text)])
        except ParsingException as e:
            AutoFix.get().error(str(e))
            return False

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and obj is self:
            if self.hasFocus():
                key = event.key()
                if key == QtCore.Qt.Key_Return:
                    if self.try_parse(self.text()):
                        self.clear()
                elif key == QtCore.Qt.Key_Up:
                    self.cmd_index -= 1
                    try:
                        self.setText(self.cmds_run[self.cmd_index])
                    except IndexError:
                        self.cmd_index = 0
                elif key == QtCore.Qt.Key_Down:
                    self.cmd_index += 1
                    if self.cmd_index < 0:
                        try:
                            self.setText(self.cmds_run[self.cmd_index])
                        except IndexError:
                            self.cmd_index = 0
                    else:
                        self.cmd_index = 0
                        self.clear()
        return super().eventFilter(obj, event)