from PyQt5.QtWidgets import QLabel, QColorDialog


class ColorWidgetHandler:
    def on_color_change(self, colorwidget, color):
        """Return True on success"""
        raise NotImplementedError()


class ColorWidget(QLabel):
    def __init__(self, color=None, text=None, handler=None):
        if color is None:
            color = (0, 0, 0, 0)
        elif not type(color) == tuple:
            raise RuntimeError('Unexpected type for color {}'.format(type(color)))
        if text:
            self.has_label = True
        else:
            self.has_label = False
            text = str(color)
        super().__init__(text)
        self.handler = handler
        self.set_color(color)

    @staticmethod
    def get_rgba255(qcolor):
        ret = []
        for x in qcolor.getRgbF():
            ret.append(int(x * 255))
        return ret

    def mouseDoubleClickEvent(self, ev):
        if self.handler:
            color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
            if color.isValid():
                color = self.get_rgba255(color)
                if self.handler.on_color_change(self, color):
                    self.set_color(color)

    def set_color(self, color):
        if not self.has_label:
            self.setText(str(color))
        self.color = color
        # todo, based on color set foreground
        s = 'rgba' + str((color[0], color[1], color[2], 255))
        self.setStyleSheet('QLabel { background-color: ' + s + ' }')

