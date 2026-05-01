from collections.abc import Iterable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QLinearGradient, QPainter, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT, RED, WINDOW_HEIGHT, WINDOW_WIDTH
from smartparts.ui.icons import IconWidget
from smartparts.ui.order_creation_window import OrderCreationCanvas
from smartparts.ui.styles import dashboard_stylesheet


class DashboardWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self.setWindowTitle("SmartParts - Рабочий стол")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(820, 560)
        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        self._exit_fullscreen_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._exit_fullscreen_shortcut.activated.connect(self._exit_fullscreen)
        self._show_dashboard()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()

    def _show_dashboard(self) -> None:
        self.setWindowTitle("SmartParts - Рабочий стол")
        canvas = DashboardCanvas(self.session)
        canvas.logout_requested.connect(self.logout_requested.emit)
        canvas.create_order_requested.connect(self._show_order_creation)
        self.setCentralWidget(canvas)

    def _show_order_creation(self) -> None:
        self.setWindowTitle("SmartParts - Создание заказа или поставки")
        canvas = OrderCreationCanvas(self.session)
        canvas.logout_requested.connect(self.logout_requested.emit)
        canvas.return_to_dashboard_requested.connect(self._show_dashboard)
        self.setCentralWidget(canvas)


class DashboardCanvas(QWidget):
    logout_requested = Signal()
    create_order_requested = Signal()

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self.setObjectName("dashboardCanvas")
        self.setStyleSheet(dashboard_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar_widget = self._sidebar()
        self._workspace_widget = self._workspace()
        root.addWidget(self._sidebar_widget)
        root.addWidget(self._workspace_widget, 1)

    def _sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(240)
        sidebar.setMaximumWidth(300)
        sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(sidebar)
        self._sidebar_layout = layout
        layout.setContentsMargins(28, 34, 28, 34)
        layout.setSpacing(24)

        layout.addWidget(self._brand_area())
        layout.addStretch(1)
        layout.addWidget(self._session_panel())
        return sidebar

    def _brand_area(self) -> QFrame:
        area = QFrame()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        accent = QFrame()
        accent.setObjectName("brandAccent")
        accent.setFixedHeight(4)
        layout.addWidget(accent)

        title = QLabel("SMARTPARTS")
        title.setObjectName("brandTitle")
        layout.addWidget(title)

        subtitle = QLabel("Рабочее место оператора")
        subtitle.setObjectName("brandSubtitle")
        layout.addWidget(subtitle)
        return area

    def _session_panel(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Пользователь")
        title.setObjectName("sessionTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("sessionCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)
        card_layout.addWidget(IconWidget("user", CYAN, 17))

        session_details = QFrame()
        session_details_layout = QVBoxLayout(session_details)
        session_details_layout.setContentsMargins(0, 0, 0, 0)
        session_details_layout.setSpacing(4)

        operator = QLabel(self.session.operator_name)
        operator.setObjectName("operatorText")
        session_details_layout.addWidget(operator)

        role = QLabel(f"Role: {self.session.system_role or 'unknown'}")
        role.setObjectName("sessionRoleText")
        role.setWordWrap(True)
        session_details_layout.addWidget(role)

        card_layout.addWidget(session_details, 1)
        card_layout.addStretch(1)
        layout.addWidget(card)

        logout = QPushButton("Выйти")
        logout.setObjectName("logoutButton")
        logout.setIcon(IconWidget.to_icon("log-out", "#8FA8B9", 17))
        logout.setIconSize(QSize(17, 17))
        logout.setCursor(Qt.PointingHandCursor)
        logout.setFixedHeight(42)
        logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout)
        return panel

    def _workspace(self) -> QFrame:
        workspace = QFrame()
        workspace.setObjectName("mainWorkspace")

        layout = QVBoxLayout(workspace)
        self._workspace_layout = layout
        layout.setContentsMargins(38, 34, 38, 34)
        layout.setSpacing(22)
        layout.addWidget(self._header())
        scroll = QScrollArea()
        scroll.setObjectName("workspaceScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._body())
        layout.addWidget(scroll, 1)
        return workspace

    def _header(self) -> QFrame:
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        text = QFrame()
        text_layout = QVBoxLayout(text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)

        title = QLabel("Рабочий стол")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Выберите режим работы или найдите запчасть по артикулу")
        subtitle.setObjectName("pageSubtitle")
        self._page_subtitle = subtitle
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        self._header_layout = layout
        self._header_text = text
        self._search_widget = self._search_box()
        layout.addWidget(text, 1)
        layout.addWidget(self._search_widget)
        return header

    def _search_box(self) -> QFrame:
        search = QFrame()
        search.setObjectName("quickSearch")
        search.setMinimumSize(260, 54)
        search.setMaximumWidth(420)
        search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(search)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(12)
        layout.addWidget(IconWidget("search", CYAN, 21))

        field = QLineEdit()
        field.setObjectName("searchInput")
        field.setPlaceholderText("Артикул, OEM или аналог")
        field.setFrame(False)
        layout.addWidget(field, 1)
        return search

    def _body(self) -> QFrame:
        body = QFrame()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(22)

        grid = QFrame()
        grid_layout = QVBoxLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(18)

        grid_layout.addLayout(
            self._card_row(
                (
                    ("file-plus", CYAN, "Создать заказ или поставку", "Быстрое оформление клиентского заказа, заявки поставщику или новой поставки на склад.", "Создать", "plus", True),
                    ("package-check", MINT, "Приемка от поставщиков", "Сверка поставки с заказом, ввод фактического количества и фиксация расхождений.", "Начать приемку", "check", False),
                )
            )
        )
        grid_layout.addLayout(
            self._card_row(
                (
                    ("shopping-bag", CYAN, "Выдача заказов", "Поиск готового заказа, контроль оплаты, печать документов и подтверждение выдачи.", "Перейти к выдаче", "send", False),
                    ("scan-search", MINT, "Проверка запчастей и аналогов", "Проверка артикула, OEM-номеров, применимости и доступных аналогов в локальной базе.", "Проверить артикул", "search", False),
                )
            )
        )

        layout.addWidget(grid, 1)
        self._summary_widget = self._summary_panel()
        layout.addWidget(self._summary_widget)
        return body

    def _card_row(self, cards: Iterable[tuple[str, str, str, str, str, str, bool]]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(18)
        for icon, color, title, description, action, action_icon, primary in cards:
            card, button = self._mode_card(icon, color, title, description, action, action_icon, primary)
            if primary:
                button.clicked.connect(self.create_order_requested.emit)
            row.addWidget(card, 1)
        return row

    def _mode_card(
        self,
        icon: str,
        color: str,
        title: str,
        description: str,
        action: str,
        action_icon: str,
        primary: bool,
    ) -> tuple[QFrame, QPushButton]:
        card = QFrame()
        card.setObjectName("modeCardPrimary" if primary else ("modeCardAccent" if color == MINT else "modeCard"))
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.addWidget(IconWidget(icon, color, 34))

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 22px;")
        content_layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setObjectName("cardDescription")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 13px; line-height: 1.35;")
        content_layout.addWidget(description_label)
        layout.addWidget(content)
        layout.addStretch(1)

        button = QPushButton(action)
        button.setObjectName("primaryAction" if primary else "secondaryAction")
        icon_color = "#061116" if primary else color
        button.setIcon(IconWidget.to_icon(action_icon, icon_color, 17))
        button.setIconSize(QSize(17, 17))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(44)
        layout.addWidget(button)
        return card, button

    def _summary_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("summaryPanel")
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(330)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Очередь на сегодня")
        title.setObjectName("summaryTitle")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        subtitle = QLabel("Короткий список задач без перехода в отдельные разделы")
        subtitle.setObjectName("summarySubtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px;")
        layout.addWidget(subtitle)

        layout.addWidget(self._task_item("Ожидают приемки", "12", "taskCountMint"))
        layout.addWidget(self._task_item("Готовы к выдаче", "8", "taskCountCyan"))
        layout.addWidget(self._task_item("Требуют проверки", "3", "taskCountRed", problem=True))
        layout.addStretch(1)
        return panel

    @staticmethod
    def _task_item(label: str, count: str, count_object: str, problem: bool = False) -> QFrame:
        item = QFrame()
        item.setObjectName("taskItemProblem" if problem else "taskItem")
        item.setFixedHeight(48)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setObjectName("taskProblemLabel" if problem else "taskLabel")
        label_widget.setStyleSheet("font-size: 13px;")
        layout.addWidget(label_widget, 1)

        count_widget = QLabel(count)
        count_widget.setObjectName(count_object)
        layout.addWidget(count_widget)
        return item

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        background = QLinearGradient(0, 0, self.width(), self.height())
        background.setColorAt(0.0, QColor("#080D12"))
        background.setColorAt(0.56, QColor("#111B25"))
        background.setColorAt(1.0, QColor("#07141A"))
        painter.fillRect(self.rect(), background)

        super().paintEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        width = self.width()
        compact = width < 1180
        narrow = width < 940

        self._summary_widget.setVisible(not compact)
        self._sidebar_widget.setMaximumWidth(240 if compact else 300)
        self._sidebar_widget.setMinimumWidth(210 if narrow else 240)
        self._sidebar_layout.setContentsMargins(18 if compact else 28, 24 if compact else 34, 18 if compact else 28, 24 if compact else 34)
        self._search_widget.setMaximumWidth(320 if compact else 420)
        self._page_subtitle.setVisible(not narrow)

        margin = 22 if compact else 38
        top_margin = 24 if compact else 34
        self._workspace_layout.setContentsMargins(margin, top_margin, margin, top_margin)
        super().resizeEvent(event)
