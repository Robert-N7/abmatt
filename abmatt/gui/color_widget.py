from PyQt5.QtWidgets import QLabel, QColorDialog


class ColorWidgetHandler:
    def on_color_change(self, colorwidget, color):
        """Return True on success"""
        raise NotImplementedError()


class ColorWidget(QLabel):
    def __init__(self, color=None, text=None, handler=None):
        if color is None:
            color = (0, 0, 0, 0)
        if text:
            self.has_label = True
        else:
            self.has_label = False
            text = str(color)
        super().__init__(text)
        self.handler = handler
        self.set_color(color)

    def mouseDoubleClickEvent(self, ev):
        if self.handler:
            color = QColorDialog.getColor()
            if color.isValid():
                if self.handler.on_color_change(self, color):
                    self.set_color(color)

    def set_color(self, color):
        if not self.has_label:
            self.setText(str(color))
        self.color = color
        # todo, based on color set foreground
        s = 'rgba' + str(color[:3])
        self.setStyleSheet('QLabel { background-color: ' + s + ' }')

