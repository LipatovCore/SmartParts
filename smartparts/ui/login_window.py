from PySide6.QtCore import QObject, QPointF, QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QKeySequence, QLinearGradient, QPainter, QPen, QBrush, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from smartparts.services.moysklad import MoySkladAuthError, authenticate
from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT, WINDOW_HEIGHT, WINDOW_WIDTH
from smartparts.ui.dashboard_window import DashboardWindow
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import login_stylesheet


class AuthWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, login: str, password: str) -> None:
        super().__init__()
        self._login = login
        self._password = password

    def run(self) -> None:
        try:
            self.succeeded.emit(authenticate(self._login, self._password))
        except MoySkladAuthError as error:
            self.failed.emit(error.message)
        except Exception:
            self.failed.emit("Не удалось выполнить вход. Попробуйте снова.")
        finally:
            self.finished.emit()


class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.dashboard_window: DashboardWindow | None = None
        self.session: AppSession | None = None
        self._auth_thread: QThread | None = None
        self._auth_worker: AuthWorker | None = None
        self.setWindowTitle("SmartParts - Вход")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(760, 520)
        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        self._exit_fullscreen_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._exit_fullscreen_shortcut.activated.connect(self._exit_fullscreen)
        canvas = LoginCanvas()
        canvas.login_requested.connect(self._authenticate)
        self.canvas = canvas
        self.setCentralWidget(canvas)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()

    def _authenticate(self, login: str, password: str) -> None:
        if self._auth_thread is not None:
            return

        self.canvas.set_busy(True)
        self._auth_thread = QThread(self)
        self._auth_worker = AuthWorker(login, password)
        self._auth_worker.moveToThread(self._auth_thread)
        self._auth_thread.started.connect(self._auth_worker.run)
        self._auth_worker.succeeded.connect(self._open_dashboard)
        self._auth_worker.failed.connect(self._show_auth_error)
        self._auth_worker.finished.connect(self._auth_thread.quit)
        self._auth_worker.finished.connect(self._auth_worker.deleteLater)
        self._auth_thread.finished.connect(self._auth_thread.deleteLater)
        self._auth_thread.finished.connect(self._clear_auth_worker)
        self._auth_thread.start()

    def _show_auth_error(self, message: str) -> None:
        self.canvas.set_busy(False)
        self.canvas.show_error(message)

    def _clear_auth_worker(self) -> None:
        self._auth_thread = None
        self._auth_worker = None

    def _open_dashboard(self, session: AppSession) -> None:
        self.session = session
        self.canvas.set_busy(False)
        self.canvas.reset()
        self.dashboard_window = DashboardWindow(session)
        self.dashboard_window.logout_requested.connect(self._logout)
        self.dashboard_window.show()
        self.hide()

    def _logout(self) -> None:
        self.session = None
        if self.dashboard_window is not None:
            self.dashboard_window.close()
            self.dashboard_window = None
        self.show()


class LoginCanvas(QWidget):
    login_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("canvas")
        self.setStyleSheet(login_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._brand_panel = self._build_brand_panel()
        self._form_zone = self._build_form_zone()
        root.addWidget(self._brand_panel)
        root.addWidget(self._form_zone, 1)

    def _build_brand_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("brandPanel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(520)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        self._brand_layout = layout
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
        form.setMinimumWidth(280)
        form.setMaximumWidth(430)
        form.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(18)

        form_layout.addLayout(self._form_header())
        self.error_box, self.error_label = self._error_box()
        form_layout.addWidget(self.error_box)
        form_layout.addLayout(self._input_group("Логин", "operator", "user", CYAN, "loginInput"))
        form_layout.addLayout(self._input_group("Пароль", "Введите пароль", "lock", CYAN, "passwordInput", password=True))
        self.login_button = self._login_button()
        form_layout.addWidget(self.login_button)
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
            line.setFixedHeight(2)
            line.setMaximumWidth(width)
            line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
    def _error_box() -> tuple[QFrame, QLabel]:
        box = QFrame()
        box.setObjectName("errorBox")
        box.setVisible(False)

        row = QHBoxLayout(box)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)
        row.addWidget(IconWidget("alert", "#FF7A85", 18))

        text = QLabel("Неверный логин или пароль")
        text.setObjectName("errorText")
        text.setWordWrap(True)
        row.addWidget(text)
        row.addStretch(1)

        return box, text

    def _input_group(
        self,
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
        line_edit.returnPressed.connect(self._submit)
        if object_name == "loginInput":
            self.login_input = line_edit
        elif object_name == "passwordInput":
            self.password_input = line_edit

        row.addWidget(line_edit, 1)
        group.addWidget(shell)
        return group

    def _login_button(self) -> QPushButton:
        button = QPushButton("Вход")
        button.setObjectName("loginButton")
        button.setIcon(IconWidget.to_icon("login", "#E7FFF9", 20))
        button.setIconSize(QSize(20, 20))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(54)
        button.clicked.connect(self._submit)
        return button

    def _submit(self) -> None:
        login = self.login_input.text().strip()
        password = self.password_input.text()
        if not login or not password:
            self.show_error("Введите логин и пароль.")
            return

        self.error_box.setVisible(False)
        self.login_requested.emit(login, password)

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_box.setVisible(True)

    def set_busy(self, busy: bool) -> None:
        self.login_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.login_button.setEnabled(not busy)
        self.login_button.setText("Подключение..." if busy else "Вход")

    def reset(self) -> None:
        self.password_input.clear()
        self.error_box.setVisible(False)
        self.set_busy(False)

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

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        width = self.width()
        compact = width < 1120
        self._brand_panel.setVisible(width >= 980)
        self._brand_panel.setMaximumWidth(520 if not compact else 400)
        self._brand_layout.setContentsMargins(40 if compact else 64, 56 if compact else 72, 40 if compact else 64, 56 if compact else 72)
        self._form_zone.layout().setContentsMargins(28, 28, 28, 28)
        super().resizeEvent(event)
