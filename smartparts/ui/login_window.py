from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget

from smartparts.theme import CYAN, MINT, WINDOW_HEIGHT, WINDOW_WIDTH
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import login_stylesheet


class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SmartParts - Вход")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setCentralWidget(LoginCanvas())


class LoginCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("canvas")
        self.setStyleSheet(login_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_brand_panel())
        root.addWidget(self._build_form_zone(), 1)

    def _build_brand_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("brandPanel")
        panel.setFixedWidth(520)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(64, 72, 64, 72)
        layout.setSpacing(34)
        layout.setAlignment(Qt.AlignVCenter)

        layout.addWidget(self._accent_bar())
        layout.addLayout(self._brand_text())
        layout.addWidget(self._diagnostics())
        layout.addWidget(IconWidget("cog", CYAN, 96))

        return panel

    def _build_form_zone(self) -> QFrame:
        zone = QFrame()
        zone.setObjectName("formZone")

        layout = QVBoxLayout(zone)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._login_form())

        return zone

    def _login_form(self) -> QFrame:
        form = QFrame()
        form.setObjectName("loginCard")
        form.setFixedWidth(430)

        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(18)

        form_layout.addLayout(self._form_header())
        form_layout.addWidget(self._error_box())
        form_layout.addLayout(self._input_group("Логин", "operator", "user", CYAN, "loginInput"))
        form_layout.addLayout(self._input_group("Пароль", "Введите пароль", "lock", CYAN, "passwordInput", password=True))
        form_layout.addWidget(self._login_button())
        form_layout.addLayout(self._footer())

        return form

    @staticmethod
    def _accent_bar() -> QFrame:
        accent = QFrame()
        accent.setObjectName("accentBar")
        accent.setFixedHeight(4)
        return accent

    @staticmethod
    def _brand_text() -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel("SMARTPARTS")
        title.setObjectName("brandTitle")

        subtitle = QLabel("Локальная система учета автозапчастей для\nоператора магазина")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    @staticmethod
    def _diagnostics() -> QWidget:
        diagnostics = QVBoxLayout()
        diagnostics.setContentsMargins(0, 0, 0, 0)
        diagnostics.setSpacing(12)

        for name, width in (("diag1", 360), ("diag2", 250), ("diag3", 340)):
            line = QFrame()
            line.setObjectName(name)
            line.setFixedSize(width, 2)
            diagnostics.addWidget(line)

        holder = QWidget()
        holder.setFixedHeight(132)
        holder.setLayout(diagnostics)
        return holder

    @staticmethod
    def _form_header() -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(8)

        title = QLabel("Вход")
        title.setObjectName("formTitle")

        caption = QLabel("Введите учетные данные сотрудника")
        caption.setObjectName("formCaption")

        header.addWidget(title)
        header.addWidget(caption)
        return header

    @staticmethod
    def _error_box() -> QFrame:
        box = QFrame()
        box.setObjectName("errorBox")
        box.setVisible(False)

        row = QHBoxLayout(box)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)
        row.addWidget(IconWidget("alert", "#FF7A85", 18))

        text = QLabel("Неверный логин или пароль")
        text.setObjectName("errorText")
        row.addWidget(text)
        row.addStretch(1)

        return box

    @staticmethod
    def _input_group(
        label_text: str,
        placeholder: str,
        icon: str,
        color: str,
        object_name: str,
        password: bool = False,
    ) -> QVBoxLayout:
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
        line_edit.setPlaceholderText(placeholder)
        line_edit.setObjectName("lineEdit")
        line_edit.setFrame(False)
        if password:
            line_edit.setEchoMode(QLineEdit.Password)

        row.addWidget(line_edit, 1)
        group.addWidget(shell)
        return group

    @staticmethod
    def _login_button() -> QPushButton:
        button = QPushButton("Вход")
        button.setObjectName("loginButton")
        button.setIcon(IconWidget.to_icon("login", "#E7FFF9", 20))
        button.setIconSize(QSize(20, 20))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(54)
        return button

    @staticmethod
    def _footer() -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addWidget(IconWidget("shield", MINT, 15))

        footer_label = QLabel("Локальная авторизация без сетевого подключения")
        footer_label.setObjectName("footerText")
        footer.addWidget(footer_label)
        footer.addStretch(1)
        return footer

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        background = QLinearGradient(0, 0, self.width(), self.height())
        background.setColorAt(0.0, QColor("#080D12"))
        background.setColorAt(0.56, QColor("#111B25"))
        background.setColorAt(1.0, QColor("#07141A"))
        painter.fillRect(self.rect(), background)

        glow = QLinearGradient(84, 716, 1282, 716)
        glow.setColorAt(0, QColor(45, 226, 230, 0))
        glow.setColorAt(0.5, QColor(45, 226, 230, 170))
        glow.setColorAt(1, QColor(50, 246, 166, 0))
        painter.setPen(QPen(QBrush(glow), 2))
        painter.drawLine(84, 716, 1282, 716)

        super().paintEvent(event)
