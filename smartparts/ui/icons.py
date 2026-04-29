from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class IconWidget(QWidget):
    """Small painted icon used by the login screen."""

    def __init__(self, kind: str, color: str, size: int = 20, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.color = QColor(color)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.color, max(1.4, self.width() / 13))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if self.kind == "user":
            self._paint_user(painter)
        elif self.kind == "lock":
            self._paint_lock(painter)
        elif self.kind == "alert":
            self._paint_alert(painter)
        elif self.kind == "login":
            self._paint_login(painter)
        elif self.kind == "shield":
            self._paint_shield(painter)
        elif self.kind == "cog":
            self._paint_cog(painter)

        super().paintEvent(event)

    @staticmethod
    def to_icon(kind: str, color: str, size: int) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        icon = IconWidget(kind, color, size)
        icon.render(pixmap)
        return QIcon(pixmap)

    def _paint_user(self, painter: QPainter) -> None:
        painter.drawEllipse(QRectF(self.width() * 0.36, 4, self.width() * 0.28, self.height() * 0.28))

        path = QPainterPath()
        path.moveTo(self.width() * 0.25, self.height() * 0.82)
        path.cubicTo(
            self.width() * 0.28,
            self.height() * 0.58,
            self.width() * 0.72,
            self.height() * 0.58,
            self.width() * 0.75,
            self.height() * 0.82,
        )
        painter.drawPath(path)

    def _paint_lock(self, painter: QPainter) -> None:
        painter.drawRoundedRect(QRectF(4, self.height() * 0.43, self.width() - 8, self.height() * 0.42), 2, 2)
        painter.drawArc(QRectF(self.width() * 0.28, 3, self.width() * 0.44, self.height() * 0.52), 0, 180 * 16)

    def _paint_alert(self, painter: QPainter) -> None:
        path = QPainterPath()
        path.moveTo(self.width() / 2, 3)
        path.lineTo(self.width() - 3, self.height() - 4)
        path.lineTo(3, self.height() - 4)
        path.closeSubpath()

        painter.drawPath(path)
        painter.drawLine(QPointF(self.width() / 2, 7), QPointF(self.width() / 2, self.height() - 8))
        painter.drawPoint(QPointF(self.width() / 2, self.height() - 5))

    def _paint_login(self, painter: QPainter) -> None:
        painter.drawLine(QPointF(4, self.height() / 2), QPointF(self.width() - 6, self.height() / 2))
        painter.drawLine(QPointF(self.width() - 10, self.height() * 0.32), QPointF(self.width() - 5, self.height() / 2))
        painter.drawLine(QPointF(self.width() - 10, self.height() * 0.68), QPointF(self.width() - 5, self.height() / 2))
        painter.drawLine(QPointF(self.width() - 4, 4), QPointF(self.width() - 4, self.height() - 4))

    def _paint_shield(self, painter: QPainter) -> None:
        path = QPainterPath()
        path.moveTo(self.width() / 2, 3)
        path.lineTo(self.width() - 4, 6)
        path.lineTo(self.width() - 6, self.height() * 0.58)
        path.cubicTo(
            self.width() - 7,
            self.height() * 0.75,
            self.width() * 0.63,
            self.height() - 3,
            self.width() / 2,
            self.height() - 2,
        )
        path.cubicTo(
            self.width() * 0.37,
            self.height() - 3,
            7,
            self.height() * 0.75,
            6,
            self.height() * 0.58,
        )
        path.lineTo(4, 6)
        path.closeSubpath()

        painter.drawPath(path)
        painter.drawLine(QPointF(self.width() * 0.32, self.height() * 0.52), QPointF(self.width() * 0.45, self.height() * 0.65))
        painter.drawLine(QPointF(self.width() * 0.45, self.height() * 0.65), QPointF(self.width() * 0.72, self.height() * 0.36))

    def _paint_cog(self, painter: QPainter) -> None:
        painter.setPen(QPen(self.color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        center = QPointF(self.width() / 2, self.height() / 2)

        for angle in range(0, 360, 45):
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.drawLine(QPointF(0, -self.height() * 0.45), QPointF(0, -self.height() * 0.34))
            painter.restore()

        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        painter.setPen(QPen(self.color, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawEllipse(rect.adjusted(12, 12, -12, -12))
        painter.drawEllipse(rect.adjusted(25, 25, -25, -25))
