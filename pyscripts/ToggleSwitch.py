from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QPaintEvent, QMouseEvent
from PyQt6.QtWidgets import QAbstractButton


class ToggleSwitch(QAbstractButton):
    statusChanged = pyqtSignal(bool)

    def __init__(self, brush=QBrush(QColor(Qt.GlobalColor.darkGreen)), parent=None):
        super().__init__(parent)
        self.m_status = False
        self.m_margin = 3
        self.m_bodyBrush = QBrush(QColor(Qt.GlobalColor.lightGray))
        self.setBrush(brush)
        self.setMinimumSize(40, 25)  # Set a minimum size for the toggle switch

    def getstatus(self):
        return self.m_status

    def setBrush(self, brush):
        self._brush = brush
        self.update()

    def brush(self):
        return getattr(self, '_brush', QBrush())

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)

        if self.isEnabled():
            if self.m_status:
                painter.setBrush(self.brush())
            else:
                painter.setBrush(QBrush(Qt.GlobalColor.black))
            painter.setOpacity(0.5 if self.m_status else 0.38)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            painter.drawRoundedRect(self.m_margin, self.m_margin,
                                    self.width() - 2 * self.m_margin, self.height() - 2 * self.m_margin, 7.5, 7.5)

            painter.setBrush(self.m_bodyBrush)
            painter.setOpacity(1.0)

            if self.m_status:
                painter.drawEllipse(self.width() - self.height(),
                                    self.m_margin,
                                    self.height() - 2 * self.m_margin, self.height() - 2 * self.m_margin)
            else:
                painter.drawEllipse(self.m_margin,
                                    self.m_margin,
                                    self.height() - 2 * self.m_margin, self.height() - 2 * self.m_margin)
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.black))
            painter.setOpacity(0.12)

            painter.drawRoundedRect(self.m_margin, self.m_margin,
                                    self.width() - 2 * self.m_margin, self.height() - 2 * self.m_margin, 7.5, 7.5)

            painter.setOpacity(1.0)
            painter.setBrush(QColor("#BDBDBD"))

            painter.drawEllipse((self.width() / 2) - (self.height() / 4),
                                self.m_margin,
                                self.height() - 2 * self.m_margin, self.height() - 2 * self.m_margin)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() & Qt.MouseButton.LeftButton:
            self.m_status = not self.m_status
            self.statusChanged.emit(self.m_status)
            self.update()

        super().mouseReleaseEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(40, 25)
