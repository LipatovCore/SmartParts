from collections.abc import Iterable
from dataclasses import replace

from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QLinearGradient, QPainter, QPen, QShortcut
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
from smartparts.services.moysklad import load_brands, load_counterparties
from smartparts.theme import CYAN, MINT, RED, WINDOW_HEIGHT, WINDOW_WIDTH
from smartparts.ui.icons import IconWidget
from smartparts.ui.order_creation_window import OrderCreationCanvas
from smartparts.ui.styles import dashboard_stylesheet


class BrandLoaderWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, access_token: str) -> None:
        super().__init__()
        self._access_token = access_token

    def run(self) -> None:
        try:
            self.succeeded.emit(load_brands(self._access_token))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class CounterpartyLoaderWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, access_token: str) -> None:
        super().__init__()
        self._access_token = access_token

    def run(self) -> None:
        try:
            self.succeeded.emit(load_counterparties(self._access_token))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class DashboardWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self.setWindowTitle("SmartParts - Рабочий стол")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(820, 560)
        self._dashboard_canvas: DashboardCanvas | None = None
        self._brands_loading = True
        self._counterparties_loading = True
        self._brand_loader_thread: QThread | None = None
        self._brand_loader_worker: BrandLoaderWorker | None = None
        self._counterparty_loader_thread: QThread | None = None
        self._counterparty_loader_worker: CounterpartyLoaderWorker | None = None
        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        self._exit_fullscreen_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._exit_fullscreen_shortcut.activated.connect(self._exit_fullscreen)
        self._show_dashboard()
        QTimer.singleShot(0, self._load_brands)
        QTimer.singleShot(0, self._load_counterparties)

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
        canvas = DashboardCanvas(self.session, self._reference_data_loading())
        self._dashboard_canvas = canvas
        canvas.logout_requested.connect(self.logout_requested.emit)
        canvas.create_order_requested.connect(self._show_order_creation)
        self.setCentralWidget(canvas)

    def _show_order_creation(self) -> None:
        self.setWindowTitle("SmartParts - Создание заказа или поставки")
        self._dashboard_canvas = None
        canvas = OrderCreationCanvas(self.session)
        canvas.logout_requested.connect(self.logout_requested.emit)
        canvas.return_to_dashboard_requested.connect(self._show_dashboard)
        self.setCentralWidget(canvas)

    def _load_brands(self) -> None:
        if self._brand_loader_thread is not None:
            return

        self._brands_loading = True
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_reference_data_loading(True)

        self._brand_loader_thread = QThread(self)
        self._brand_loader_worker = BrandLoaderWorker(self.session.access_token)
        self._brand_loader_worker.moveToThread(self._brand_loader_thread)
        self._brand_loader_thread.started.connect(self._brand_loader_worker.run)
        self._brand_loader_worker.succeeded.connect(self._apply_loaded_brands)
        self._brand_loader_worker.failed.connect(self._handle_brand_load_error)
        self._brand_loader_worker.finished.connect(self._brand_loader_thread.quit)
        self._brand_loader_worker.finished.connect(self._brand_loader_worker.deleteLater)
        self._brand_loader_thread.finished.connect(self._brand_loader_thread.deleteLater)
        self._brand_loader_thread.finished.connect(self._clear_brand_loader)
        self._brand_loader_thread.start()

    def _apply_loaded_brands(self, brands: object) -> None:
        self.session = replace(self.session, brands=tuple(brands))
        self._brands_loading = False
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_session(self.session)
            self._dashboard_canvas.set_reference_data_loading(self._reference_data_loading())

    def _handle_brand_load_error(self, message: str) -> None:
        print(f"Failed to load MoySklad brands: {message}", flush=True)
        self._brands_loading = False
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_reference_data_loading(self._reference_data_loading())

    def _clear_brand_loader(self) -> None:
        self._brand_loader_thread = None
        self._brand_loader_worker = None

    def _load_counterparties(self) -> None:
        if self._counterparty_loader_thread is not None:
            return

        self._counterparties_loading = True
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_reference_data_loading(True)

        self._counterparty_loader_thread = QThread(self)
        self._counterparty_loader_worker = CounterpartyLoaderWorker(self.session.access_token)
        self._counterparty_loader_worker.moveToThread(self._counterparty_loader_thread)
        self._counterparty_loader_thread.started.connect(self._counterparty_loader_worker.run)
        self._counterparty_loader_worker.succeeded.connect(self._apply_loaded_counterparties)
        self._counterparty_loader_worker.failed.connect(self._handle_counterparty_load_error)
        self._counterparty_loader_worker.finished.connect(self._counterparty_loader_thread.quit)
        self._counterparty_loader_worker.finished.connect(self._counterparty_loader_worker.deleteLater)
        self._counterparty_loader_thread.finished.connect(self._counterparty_loader_thread.deleteLater)
        self._counterparty_loader_thread.finished.connect(self._clear_counterparty_loader)
        self._counterparty_loader_thread.start()

    def _apply_loaded_counterparties(self, counterparties: object) -> None:
        loaded_counterparties = tuple(counterparties)
        print(f"Loaded MoySklad counterparties: {len(loaded_counterparties)}", flush=True)
        self.session = replace(self.session, counterparties=loaded_counterparties)
        self._counterparties_loading = False
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_session(self.session)
            self._dashboard_canvas.set_reference_data_loading(self._reference_data_loading())

    def _handle_counterparty_load_error(self, message: str) -> None:
        print(f"Failed to load MoySklad counterparties: {message}", flush=True)
        self._counterparties_loading = False
        if self._dashboard_canvas is not None:
            self._dashboard_canvas.set_reference_data_loading(self._reference_data_loading())

    def _clear_counterparty_loader(self) -> None:
        self._counterparty_loader_thread = None
        self._counterparty_loader_worker = None

    def _reference_data_loading(self) -> bool:
        return self._brands_loading or self._counterparties_loading


class SpinningLoaderIcon(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(17, 17)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)

    def _tick(self) -> None:
        self._angle = (self._angle + 18) % 360
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(CYAN), 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(self.rect().adjusted(2, 2, -2, -2), self._angle * 16, 270 * 16)


class DashboardCanvas(QWidget):
    logout_requested = Signal()
    create_order_requested = Signal()

    def __init__(self, session: AppSession, brands_loading: bool = False) -> None:
        super().__init__()
        self.session = session
        self._mode_buttons: list[QPushButton] = []
        self._reference_data_loading = brands_loading
        self.setObjectName("dashboardCanvas")
        self.setStyleSheet(dashboard_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar_widget = self._sidebar()
        self._workspace_widget = self._workspace()
        root.addWidget(self._sidebar_widget)
        root.addWidget(self._workspace_widget, 1)
        self.set_reference_data_loading(brands_loading)

    def set_session(self, session: AppSession) -> None:
        self.session = session

    def set_reference_data_loading(self, loading: bool) -> None:
        self._reference_data_loading = loading
        self._brands_loading_status.setVisible(loading)
        for button in self._mode_buttons:
            button.setEnabled(not loading)

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
        self._brands_loading_status = self._brands_loading_card()
        layout.addWidget(self._brands_loading_status)
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

    def _brands_loading_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("brandsLoadingStatus")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(SpinningLoaderIcon())

        text = QFrame()
        text_layout = QVBoxLayout(text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        title = QLabel("Загрузка справочников")
        title.setObjectName("brandsLoadingTitle")
        text_layout.addWidget(title)

        subtitle = QLabel("Бренды и контрагенты")
        subtitle.setObjectName("brandsLoadingSubtitle")
        text_layout.addWidget(subtitle)

        layout.addWidget(text, 1)
        return card

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
            self._mode_buttons.append(button)
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
