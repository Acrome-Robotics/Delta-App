import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, pyqtSignal, QPointF

class XYPadWidget(QWidget):
    positionChanged = pyqtSignal(float, float) # Emits x, y in physical units

    def __init__(self, x_min=-100.0, x_max=100.0, y_min=-100.0, y_max=100.0, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)

        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        # Current physical position
        self.curr_x = 0.0
        self.curr_y = 0.0

        self.is_dragging = False

    def get_pixel_pos(self):
        """Converts current physical x, y to pixel coordinates."""
        w = self.width() - 1
        h = self.height() - 1

        px = ((self.curr_x - self.x_min) / (self.x_max - self.x_min)) * w
        
        # UI Y is top-to-bottom, Physical Y is bottom-to-top 
        # Wait, Acrome Delta X goes right, Y goes out.
        # Let's map Y conventionally: Top is +Y, Bottom is -Y
        py = ((self.y_max - self.curr_y) / (self.y_max - self.y_min)) * h

        return px, py

    def update_position_from_pixel(self, px, py):
        w = self.width() - 1
        h = self.height() - 1

        # Clamp pixels
        px = max(0, min(w, px))
        py = max(0, min(h, py))

        cx = self.x_min + (px / w) * (self.x_max - self.x_min)
        cy = self.y_max - (py / h) * (self.y_max - self.y_min)

        if cx != self.curr_x or cy != self.curr_y:
            self.curr_x = cx
            self.curr_y = cy
            self.positionChanged.emit(self.curr_x, self.curr_y)
            self.update()

    def set_position(self, x, y):
        """Update position from external source if not dragging."""
        if self.is_dragging: return
        
        x = max(self.x_min, min(self.x_max, x))
        y = max(self.y_min, min(self.y_max, y))
        
        if self.curr_x != x or self.curr_y != y:
            self.curr_x = x
            self.curr_y = y
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.update_position_from_pixel(event.x(), event.y())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update_position_from_pixel(event.x(), event.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        # Add Border
        pen = QPen(QColor("#45475a"), 2)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

        # Draw Crosshair
        w = self.width()
        h = self.height()
        painter.setPen(QPen(QColor("#313244"), 1, Qt.DashLine))
        
        # Zero lines
        zero_px, zero_py = self.get_pixel_pos()
        # Find physical zero
        zero_x_px = ((0 - self.x_min) / (self.x_max - self.x_min)) * w
        zero_y_px = ((self.y_max - 0) / (self.y_max - self.y_min)) * h
        
        painter.drawLine(int(zero_x_px), 0, int(zero_x_px), h)
        painter.drawLine(0, int(zero_y_px), w, int(zero_y_px))

        # Draw Dot
        px, py = self.get_pixel_pos()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#f38ba8")))
        painter.drawEllipse(QPointF(px, py), 6, 6)

        painter.end()
