from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
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

    ARTICLE_SEARCH_URL = "https://www.abcp.ru/crossbase/api#articles_info"

    _MODES = {
        "exact": {
            "button": "Точные совпадения",
            "headers": ("Наименование", "Артикул", "Бренд", "Кол-во", "Ячейка"),
            "rows": (
                ("Фильтр масляный BMW N47", "11428507683", "BMW", "3", "A-12-04"),
                ("Фильтр масляный аналог", "11428507683", "BMW OEM", "1", "B-03-11"),
                ("Картридж масляного фильтра", "11428507683", "BMW", "5", "C-08-02"),
            ),
        },
        "stock": {
            "button": "Есть в МойСклад",
            "headers": ("Наименование", "Артикул", "Бренд", "Кол-во", "Ячейка"),
            "rows": (
                ("Фильтр масляный BMW N47", "11428507683", "BMW", "3", "A-12-04"),
                ("Фильтр масляный аналог", "11428507683", "BMW OEM", "1", "B-03-11"),
                ("Картридж масляного фильтра", "11428507683", "BMW", "5", "C-08-02"),
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
        self._active_section = "paste"
        self._selected_mode = "exact"
        self._mode_buttons: dict[str, QPushButton] = {}
        self._section_buttons: dict[str, QPushButton] = {}
        self.setObjectName("articleCheckCanvas")
        self.setStyleSheet(article_check_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar_widget = self._sidebar()
        self._workspace_widget = self._workspace()
        root.addWidget(self._sidebar_widget)
        root.addWidget(self._workspace_widget, 1)
        self._show_section("paste")
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
        layout.addWidget(self._section_switcher())
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

    def _section_switcher(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Проверка")
        title.setObjectName("sessionTitle")
        layout.addWidget(title)

        for key, text, icon in (
            ("paste", "Вставка страницы", "file-plus"),
            ("results", "Результаты", "package-check"),
        ):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setIcon(IconWidget.to_icon(icon, "#8FA8B9", 16))
            button.setIconSize(QSize(16, 16))
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(38)
            button.clicked.connect(lambda checked=False, section=key: self._show_section(section))
            self._section_buttons[key] = button
            layout.addWidget(button)
        return panel

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

        self._stack = QStackedWidget()
        self._stack.setObjectName("articlePageStack")
        self._stack.addWidget(self._paste_page())
        self._stack.addWidget(self._results_page())
        layout.addWidget(self._stack, 1)
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

        self._page_title = QLabel()
        self._page_title.setObjectName("pageTitle")
        self._page_subtitle = QLabel()
        self._page_subtitle.setObjectName("pageSubtitle")
        self._page_subtitle.setWordWrap(True)
        text_layout.addWidget(self._page_title)
        text_layout.addWidget(self._page_subtitle)

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

    def _paste_page(self) -> QFrame:
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        panel = QFrame()
        panel.setObjectName("pastePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        instruction_title = QLabel("Как все сделать")
        instruction_title.setObjectName("instructionTitle")
        panel_layout.addWidget(instruction_title)

        instruction = QLabel(
            "1. Нажмите «Открыть сайт».\n"
            "2. На сайте вставьте нужный артикул, выберите бренд и выполните поиск.\n"
            "3. Скопируйте всю страницу через Ctrl+A и Ctrl+C.\n"
            "4. Вернитесь сюда, вставьте текст страницы в большое поле и нажмите «Отправить»."
        )
        instruction.setObjectName("instructionText")
        instruction.setWordWrap(True)
        panel_layout.addWidget(instruction)

        open_site = QPushButton("Открыть сайт")
        open_site.setObjectName("secondaryAction")
        open_site.setIcon(IconWidget.to_icon("search", CYAN, 16))
        open_site.setIconSize(QSize(16, 16))
        open_site.setCursor(Qt.PointingHandCursor)
        open_site.setFixedSize(156, 40)
        open_site.clicked.connect(self._open_article_site)
        panel_layout.addWidget(open_site)

        label = QLabel("Скопированная страница")
        label.setObjectName("fieldLabel")
        panel_layout.addWidget(label)

        self._page_text = QTextEdit()
        self._page_text.setObjectName("pagePasteInput")
        self._page_text.setPlaceholderText("Вставьте сюда текст страницы после Ctrl+A и Ctrl+C...")
        self._page_text.setMinimumHeight(270)
        panel_layout.addWidget(self._page_text, 1)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)
        hint = QLabel("После отправки программа выделит аналоги и покажет результат в выбранном режиме.")
        hint.setObjectName("instructionText")
        hint.setWordWrap(True)
        actions.addWidget(hint, 1)

        submit = QPushButton("Отправить")
        submit.setObjectName("primaryAction")
        submit.setIcon(IconWidget.to_icon("send", "#061116", 16))
        submit.setIconSize(QSize(16, 16))
        submit.setCursor(Qt.PointingHandCursor)
        submit.setFixedSize(150, 42)
        submit.clicked.connect(self._submit_page_text)
        actions.addWidget(submit)
        panel_layout.addLayout(actions)

        layout.addWidget(panel, 1)
        return page

    def _results_page(self) -> QFrame:
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._mode_switcher())
        self._table = self._results_table()
        layout.addWidget(self._table, 1)
        return page

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

    def _show_section(self, section: str) -> None:
        self._active_section = section
        if hasattr(self, "_stack"):
            self._stack.setCurrentIndex(0 if section == "paste" else 1)
        if hasattr(self, "_page_title"):
            if section == "paste":
                self._page_title.setText("Вставка страницы с аналогами")
                self._page_subtitle.setText("Откройте сайт, найдите артикул по бренду, скопируйте страницу и отправьте ее на разбор")
            else:
                self._page_title.setText("Результаты разбора страницы")
                self._page_subtitle.setText("Точные совпадения, наличие в МойСклад и аналоги из скопированной страницы")
        self._refresh_section_buttons()

    def _refresh_section_buttons(self) -> None:
        for key, button in self._section_buttons.items():
            active = key == self._active_section
            button.setObjectName("navActive" if active else "navButton")
            color = CYAN if active else "#8FA8B9"
            icon = "file-plus" if key == "paste" else "package-check"
            button.setIcon(IconWidget.to_icon(icon, color, 16))
            button.style().unpolish(button)
            button.style().polish(button)

    def _open_article_site(self) -> None:
        QDesktopServices.openUrl(QUrl(self.ARTICLE_SEARCH_URL))

    def _submit_page_text(self) -> None:
        self._show_section("results")
        self._render_table()

    def _set_mode(self, mode: str) -> None:
        self._selected_mode = mode
        for key, button in self._mode_buttons.items():
            button.setObjectName("modeToggleActive" if key == mode else "modeToggleInactive")
            button.style().unpolish(button)
            button.style().polish(button)
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
                quantity_column = 3
                if column_index == quantity_column and self._selected_mode != "analogs":
                    item.setForeground(QColor(MINT))
                    item.setTextAlignment(Qt.AlignCenter)
                elif column_index > 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row_index, column_index, item)

    def _filtered_rows(self, rows: tuple[tuple[str, ...], ...]) -> list[tuple[str, ...]]:
        pasted_text = self._page_text.toPlainText().strip().casefold() if hasattr(self, "_page_text") else ""
        tokens = [token for token in pasted_text.replace("-", " ").split() if len(token) >= 4]
        if not tokens:
            return list(rows)

        filtered = []
        for row in rows:
            haystack = " ".join(row).casefold()
            if any(token in haystack for token in tokens[:50]):
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
