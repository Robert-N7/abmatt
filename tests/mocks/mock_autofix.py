from abmatt.autofix import MessageReceiver


class AutoFixMock(MessageReceiver):
    def info(self, message):
        self.infos.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)

    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []
