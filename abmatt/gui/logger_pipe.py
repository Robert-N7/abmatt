from PyQt5.QtCore import QObject, pyqtSignal

from abmatt.autofix import MessageReceiver, AutoFix


class LoggerPipe(QObject, MessageReceiver):
    info_sig = pyqtSignal(str)
    warn_sig = pyqtSignal(str)
    error_sig = pyqtSignal(str)

    def info(self, message):
        if not self.signalsBlocked():
            self.info_sig.emit(message)

    def warn(self, message):
        if not self.signalsBlocked():
            self.warn_sig.emit(message)

    def error(self, message):
        if not self.signalsBlocked():
            self.error_sig.emit(message)

    def __init__(self):
        super().__init__()
        AutoFix.set_pipe(self)