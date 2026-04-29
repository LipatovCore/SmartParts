import sys

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


CYAN = "#2DE2E6"
MINT = "#32F6A6"
RED = "#FF5E6C"


class IconWidget(QWidget):
    def __init__(self, kind, color, size=20, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = QColor(color)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.color, max(1.4, self.width() / 13))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        if self.kind == "user":
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
        elif self.kind == "lock":
            painter.drawRoundedRect(QRectF(4, self.height() * 0.43, self.width() - 8, self.height() * 0.42), 2, 2)
            painter.drawArc(QRectF(self.width() * 0.28, 3, self.width() * 0.44, self.height() * 0.52), 0, 180 * 16)
        elif self.kind == "alert":
            path = QPainterPath()
            path.moveTo(self.width() / 2, 3)
            path.lineTo(self.width() - 3, self.height() - 4)
            path.lineTo(3, self.height() - 4)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(self.width() / 2, 7), QPointF(self.width() / 2, self.height() - 8))
            painter.drawPoint(QPointF(self.width() / 2, self.height() - 5))
        elif self.kind == "login":
            painter.drawLine(QPointF(4, self.height() / 2), QPointF(self.width() - 6, self.height() / 2))
            painter.drawLine(QPointF(self.width() - 10, self.height() * 0.32), QPointF(self.width() - 5, self.height() / 2))
            painter.drawLine(QPointF(self.width() - 10, self.height() * 0.68), QPointF(self.width() - 5, self.height() / 2))
            painter.drawLine(QPointF(self.width() - 4, 4), QPointF(self.width() - 4, self.height() - 4))
        elif self.kind == "shield":
            path = QPainterPath()
            path.moveTo(self.width() / 2, 3)
            path.lineTo(self.width() - 4, 6)
            path.lineTo(self.width() - 6, self.height() * 0.58)
            path.cubicTo(self.width() - 7, self.height() * 0.75, self.width() * 0.63, self.height() - 3, self.width() / 2, self.height() - 2)
            path.cubicTo(self.width() * 0.37, self.height() - 3, 7, self.height() * 0.75, 6, self.height() * 0.58)
            path.lineTo(4, 6)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(self.width() * 0.32, self.height() * 0.52), QPointF(self.width() * 0.45, self.height() * 0.65))
            painter.drawLine(QPointF(self.width() * 0.45, self.height() * 0.65), QPointF(self.width() * 0.72, self.height() * 0.36))
        elif self.kind == "cog":
            painter.setPen(QPen(self.color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            center = QPointF(self.width() / 2, self.height() / 2)
            for angle in range(0, 360, 45):
                painter.save()
                painter.translate(center)
                painter.rotate(angle)
                painter.drawLine(QPointF(0, -self.height() * 0.45), QPointF(0, -self.height() * 0.34))
                painter.restore()
            painter.setPen(QPen(self.color, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawEllipse(rect.adjusted(12, 12, -12, -12))
            painter.drawEllipse(rect.adjusted(25, 25, -25, -25))


class SciFiLoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartParts - Login")
        self.setFixedSize(1366, 768)
        self.setCentralWidget(LoginCanvas())


class LoginCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("canvas")
        self.setStyleSheet(self.stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        brand = self.build_brand_panel()
        form_zone = self.build_form_zone()
        root.addWidget(brand)
        root.addWidget(form_zone, 1)

    def build_brand_panel(self):
        panel = QFrame()
        panel.setObjectName("brandPanel")
        panel.setFixedWidth(520)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(64, 72, 64, 72)
        layout.setSpacing(34)
        layout.setAlignment(Qt.AlignVCenter)

        accent = QFrame()
        accent.setObjectName("accentBar")
        accent.setFixedHeight(4)
        layout.addWidget(accent)

        title = QLabel("SMARTPARTS")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Локальная система учета автозапчастей для\nоператора магазина")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setWordWrap(True)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(10)
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        layout.addLayout(brand_text)

        diagnostics = QVBoxLayout()
        diagnostics.setContentsMargins(0, 0, 0, 0)
        diagnostics.setSpacing(12)
        for name, width in (("diag1", 360), ("diag2", 250), ("diag3", 340)):
            line = QFrame()
            line.setObjectName(name)
            line.setFixedSize(width, 2)
            diagnostics.addWidget(line)
        diagnostic_holder = QWidget()
        diagnostic_holder.setFixedHeight(132)
        diagnostic_holder.setLayout(diagnostics)
        layout.addWidget(diagnostic_holder)

        cog = IconWidget("cog", CYAN, 96)
        cog.setWindowOpacity(0.72)
        layout.addWidget(cog)
        return panel

    def build_form_zone(self):
        zone = QFrame()
        zone.setObjectName("formZone")
        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        form = QFrame()
        form.setObjectName("loginCard")
        form.setFixedWidth(430)
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(8)
        title = QLabel("Вход")
        title.setObjectName("formTitle")
        caption = QLabel("Введите учетные данные сотрудника")
        caption.setObjectName("formCaption")
        header.addWidget(title)
        header.addWidget(caption)
        form_layout.addLayout(header)

        form_layout.addWidget(self.error_box())
        form_layout.addLayout(self.input_group("Логин", "operator", "user", CYAN, "loginInput", False))
        form_layout.addLayout(self.input_group("Пароль", "••••••••", "lock", RED, "passwordInput", True))

        button = QPushButton("Вход")
        button.setObjectName("loginButton")
        button.setIcon(self.make_icon("login", "#E7FFF9", 20))
        button.setIconSize(QSize(20, 20))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(54)
        form_layout.addWidget(button)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addWidget(IconWidget("shield", MINT, 15))
        footer_label = QLabel("Локальная авторизация без сетевого подключения")
        footer_label.setObjectName("footerText")
        footer.addWidget(footer_label)
        footer.addStretch(1)
        form_layout.addLayout(footer)

        layout.addWidget(form)
        return zone

    def error_box(self):
        box = QFrame()
        box.setObjectName("errorBox")
        row = QHBoxLayout(box)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)
        row.addWidget(IconWidget("alert", "#FF7A85", 18))
        text = QLabel("Неверный логин или пароль")
        text.setObjectName("errorText")
        row.addWidget(text)
        row.addStretch(1)
        return box

    def input_group(self, label_text, value, icon, color, object_name, password):
        group = QVBoxLayout()
        group.setSpacing(8)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        group.addWidget(label)

        shell = QFrame()
        shell.setObjectName(object_name)
        shell.setFixedHeight(52)
        row = QHBoxLayout(shell)
        row.setContentsMargins(15, 0, 15, 0)
        row.setSpacing(12)
        row.addWidget(IconWidget(icon, color, 20))

        line_edit = QLineEdit()
        line_edit.setText(value)
        line_edit.setObjectName("lineEdit")
        line_edit.setFrame(False)
        if password:
            line_edit.setEchoMode(QLineEdit.Password)
        row.addWidget(line_edit, 1)
        group.addWidget(shell)
        return group

    @staticmethod
    def make_icon(kind, color, size):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        icon = IconWidget(kind, color, size)
        icon.render(pixmap)
        return QIcon(pixmap)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QLinearGradient(0, 0, self.width(), self.height())
        bg.setColorAt(0.0, QColor("#080D12"))
        bg.setColorAt(0.56, QColor("#111B25"))
        bg.setColorAt(1.0, QColor("#07141A"))
        painter.fillRect(self.rect(), bg)

        glow = QLinearGradient(84, 716, 1282, 716)
        glow.setColorAt(0, QColor(45, 226, 230, 0))
        glow.setColorAt(0.5, QColor(45, 226, 230, 170))
        glow.setColorAt(1, QColor(50, 246, 166, 0))
        painter.setPen(QPen(QBrush(glow), 2))
        painter.drawLine(84, 716, 1282, 716)

        super().paintEvent(event)

    @staticmethod
    def stylesheet():
        return f"""
        #canvas {{
            background: transparent;
            font-family: Arial;
        }}
        #brandPanel {{
            background: #0B1219;
            border-right: 1px solid #263948;
        }}
        #formZone {{
            background: #111A23;
        }}
        #accentBar {{
            border-radius: 2px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
        }}
        #brandTitle {{
            color: #F2FAFF;
            font-size: 42px;
            font-weight: 700;
        }}
        #brandSubtitle {{
            color: #9EB4C3;
            font-size: 18px;
            line-height: 1.35;
        }}
        #diag1 {{
            background: rgba(45, 226, 230, 0.20);
            border-radius: 1px;
        }}
        #diag2 {{
            background: rgba(50, 246, 166, 0.40);
            border-radius: 1px;
        }}
        #diag3 {{
            background: rgba(108, 127, 140, 0.40);
            border-radius: 1px;
        }}
        #loginCard {{
            background: transparent;
        }}
        #formTitle {{
            color: #F4FAFF;
            font-size: 40px;
            font-weight: 700;
        }}
        #formCaption {{
            color: #8FA8B9;
            font-size: 16px;
        }}
        #errorBox {{
            background: #2A171B;
            border: 1px solid {RED};
            border-radius: 6px;
        }}
        #errorText {{
            color: #FFD4D8;
            font-size: 14px;
            font-weight: 600;
        }}
        #fieldLabel {{
            color: #B7CBD9;
            font-size: 14px;
            font-weight: 700;
        }}
        #loginInput {{
            background: #0B141C;
            border: 1px solid rgba(45, 226, 230, 0.60);
            border-radius: 6px;
        }}
        #passwordInput {{
            background: #0B141C;
            border: 1px solid {RED};
            border-radius: 6px;
        }}
        #lineEdit {{
            color: #DDEAF2;
            background: transparent;
            font-size: 16px;
            selection-background-color: {CYAN};
            selection-color: #061116;
        }}
        #loginButton {{
            color: #061116;
            font-size: 16px;
            font-weight: 700;
            border: 1px solid #A9FFF0;
            border-radius: 6px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {MINT});
            padding: 0 18px;
        }}
        #loginButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5AF7FA, stop:1 #5DFFC0);
        }}
        #loginButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #19C9CD, stop:1 #25D98C);
        }}
        #footerText {{
            color: #8FA8B9;
            font-size: 11px;
        }}
        """


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial"))
    window = SciFiLoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
