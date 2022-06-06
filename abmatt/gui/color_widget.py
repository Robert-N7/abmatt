from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QColorDialog


class ColorWidgetHandler:
    def on_color_change(self, colorwidget, color):
        """Return True on success"""
        raise NotImplementedError()


class ColorWidget(QLabel):
    def __init__(self, color=None, text=None, handler=None):
        if color is None:
            color = (0, 0, 0, 0)
        elif type(color) not in (list, tuple):
            raise RuntimeError('Unexpected type for color {}'.format(type(color)))
        elif len(color) < 4:
            color = list(color)
            color.append(255)
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
        initial = self.color
        color = QColorDialog.getColor(QColor(initial[0], initial[1], initial[2], initial[3]),
                                      options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            color = self.get_rgba255(color)
            if not self.handler or self.handler.on_color_change(self, color):
                self.set_color(color)

    def set_color(self, color):
        if not self.has_label:
            self.setText(' ' * 4 + ','.join([str(x) for x in color]))
        self.color = color
        tcolor = 'white' if sum(color[:3]) < 128 * 3 else 'black'
        self.setStyleSheet(
            f'background-color: rgba{(color[0], color[1], color[2], 255)}; '
            f'color: {tcolor}; '
            f'padding: 5px; '
        )

