from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import article_check_stylesheet


class ArticleCheckCanvas(QWidget):
    logout_requested = Signal()
    return_to_dashboard_requested = Signal()

    _MODES = {
        "exact": {
            "button": "Точные совпадения",
            "headers": ("Наименование", "Артикул", "Бренд", "Кол-во", "Ячейка"),
            "rows": (
                ("Фильтр масляный BMW N47", "11428507683", "BMW", "3", "A-12-04"),
                ("Фильтр масляный найден по артикулу", "11428507683", "BMW OEM", "1", "B-03-11"),
                ("Прокладка корпуса фильтра", "11428507683", "BMW", "5", "C-08-02"),
            ),
        },
        "stock": {
            "button": "По артикулу",
            "headers": ("Наименование", "Артикул", "Кол-во", "Ячейка"),
            "rows": (
                ("Фильтр масляный BMW N47", "11428507683", "3", "A-12-04"),
                ("Фильтр масляный найден по артикулу", "11428507683", "1", "B-03-11"),
                ("Прокладка корпуса фильтра", "11428507683", "5", "C-08-02"),
            ),
        },
        "analogs": {
            "button": "Аналоги",
            "headers": ("Наименование", "Бренд", "Артикул"),
            "rows": (
                ("Аналог масляного фильтра", "MANN", "HU 7028 z"),
                ("Фильтр масляный аналог", "KNECHT", "OX 404D"),
                ("Картридж масляного фильтра аналог", "FILTRON", "OE 672/7"),
            ),
        },
    }

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self._selected_mode = "exact"
        self._mode_buttons: dict[str, QPushButton] = {}
        self.setObjectName("articleCheckCanvas")
        self.setStyleSheet(article_check_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar_widget = self._sidebar()
        self._workspace_widget = self._workspace()
        root.addWidget(self._sidebar_widget)
        root.addWidget(self._workspace_widget, 1)
        self._set_mode("exact")

    def _sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(244)

        layout = QVBoxLayout(sidebar)
        self._sidebar_layout = layout
        layout.setContentsMargins(22, 30, 22, 30)
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

        subtitle = QLabel("Проверка артикула")
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

        details = QFrame()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(4)

        operator = QLabel(self.session.operator_name)
        operator.setObjectName("operatorText")
        details_layout.addWidget(operator)

        role = QLabel(f"Role: {self.session.system_role or 'unknown'}")
        role.setObjectName("sessionRoleText")
        role.setWordWrap(True)
        details_layout.addWidget(role)

        card_layout.addWidget(details, 1)
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
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(16)
        layout.addWidget(self._header())
        layout.addWidget(self._search_row())
        layout.addWidget(self._mode_switcher())
        self._table = self._results_table()
        layout.addWidget(self._table, 1)
        return workspace

    def _header(self) -> QFrame:
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        text = QFrame()
        text_layout = QVBoxLayout(text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)

        title = QLabel("Проверка артикула")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Поиск по МойСклад, точных аналогов или похожего артикула")
        subtitle.setObjectName("pageSubtitle")
        self._page_subtitle = subtitle
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        back = QPushButton("На главную")
        back.setObjectName("backToDashboardButton")
        back.setIcon(IconWidget.to_icon("arrow-left", CYAN, 16))
        back.setIconSize(QSize(16, 16))
        back.setCursor(Qt.PointingHandCursor)
        back.setFixedSize(132, 38)
        back.clicked.connect(self.return_to_dashboard_requested.emit)

        layout.addWidget(text, 1)
        layout.addWidget(back)
        return header

    def _search_row(self) -> QFrame:
        row = QFrame()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        field_panel = QFrame()
        field_layout = QVBoxLayout(field_panel)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(6)

        label = QLabel("Поиск")
        label.setObjectName("fieldLabel")
        field_layout.addWidget(label)

        shell = QFrame()
        shell.setObjectName("articleSearchShell")
        shell.setFixedHeight(42)
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(14, 0, 14, 0)
        shell_layout.setSpacing(10)
        shell_layout.addWidget(IconWidget("search", CYAN, 16))

        self._search_input = QLineEdit("BMW 11428507683")
        self._search_input.setObjectName("articleSearchInput")
        self._search_input.setFrame(False)
        self._search_input.returnPressed.connect(self._apply_filter)
        shell_layout.addWidget(self._search_input, 1)
        field_layout.addWidget(shell)

        check = QPushButton("Проверить")
        check.setObjectName("primaryAction")
        check.setIcon(IconWidget.to_icon("search", "#061116", 16))
        check.setIconSize(QSize(16, 16))
        check.setCursor(Qt.PointingHandCursor)
        check.setFixedSize(132, 42)
        check.clicked.connect(self._apply_filter)

        layout.addWidget(field_panel, 1)
        layout.addWidget(check, 0, Qt.AlignBottom)
        return row

    def _mode_switcher(self) -> QFrame:
        switcher = QFrame()
        switcher.setObjectName("modeSwitcher")
        layout = QHBoxLayout(switcher)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        for key, config in self._MODES.items():
            button = QPushButton(config["button"])
            button.setObjectName("modeToggleInactive")
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(36)
            button.clicked.connect(lambda checked=False, mode=key: self._set_mode(mode))
            self._mode_buttons[key] = button
            layout.addWidget(button, 1)
        return switcher

    def _results_table(self) -> QTableWidget:
        table = QTableWidget(0, 4)
        table.setObjectName("articleResultsTable")
        table.setFrameShape(QFrame.NoFrame)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(52)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return table

    def _set_mode(self, mode: str) -> None:
        self._selected_mode = mode
        for key, button in self._mode_buttons.items():
            button.setObjectName("modeToggleActive" if key == mode else "modeToggleInactive")
            button.style().unpolish(button)
            button.style().polish(button)
        self._render_table()

    def _apply_filter(self) -> None:
        self._render_table()

    def _render_table(self) -> None:
        if not hasattr(self, "_table"):
            return

        config = self._MODES[self._selected_mode]
        headers = config["headers"]
        rows = self._filtered_rows(config["rows"])
        self._table.clear()
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                quantity_column = 3 if self._selected_mode == "exact" else 2
                if column_index == quantity_column and self._selected_mode != "analogs":
                    item.setForeground(QColor(MINT))
                    item.setTextAlignment(Qt.AlignCenter)
                elif column_index > 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_index, column_index, item)

    def _filtered_rows(self, rows: tuple[tuple[str, ...], ...]) -> list[tuple[str, ...]]:
        query = self._search_input.text().strip().casefold() if hasattr(self, "_search_input") else ""
        tokens = [token for token in query.replace("-", " ").split() if token]
        if not tokens:
            return list(rows)

        filtered = []
        for row in rows:
            haystack = " ".join(row).casefold()
            if any(token in haystack for token in tokens):
                filtered.append(row)
        return filtered or list(rows)

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
        compact = self.width() < 1060
        self._sidebar_widget.setFixedWidth(210 if compact else 244)
        self._sidebar_layout.setContentsMargins(18 if compact else 22, 24 if compact else 30, 18 if compact else 22, 24 if compact else 30)
        margin = 24 if compact else 34
        self._workspace_layout.setContentsMargins(margin, 24 if compact else 28, margin, 24 if compact else 28)
        self._page_subtitle.setVisible(self.width() >= 900)
        super().resizeEvent(event)
