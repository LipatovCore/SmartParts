import json
from json import JSONDecodeError
from typing import Any

from PySide6.QtCore import QObject, QSize, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from smartparts.services.moysklad import ArticleLookupItem, ProductStockMatch, find_article_stock
from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import article_check_stylesheet


class StockLookupWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, access_token: str, warehouse_id: str, items: list[ArticleLookupItem]) -> None:
        super().__init__()
        self._access_token = access_token
        self._warehouse_id = warehouse_id
        self._items = items

    def run(self) -> None:
        print(
            f"[ArticleCheck] Worker started: warehouse_id={self._warehouse_id}, lookup_items={len(self._items)}",
            flush=True,
        )
        try:
            rows = find_article_stock(self._access_token, self._warehouse_id, self._items)
            print(f"[ArticleCheck] Worker succeeded: stock_rows={len(rows)}", flush=True)
            self.succeeded.emit(rows)
        except Exception as error:  # noqa: BLE001 - show API errors in the UI without crashing the Qt thread
            message = getattr(error, "message", "") or str(error) or "Не удалось проверить наличие в МойСклад."
            print(f"[ArticleCheck] Worker failed: {message}", flush=True)
            self.failed.emit(message)
        finally:
            print("[ArticleCheck] Worker finished", flush=True)
            self.finished.emit()


class ArticleCheckCanvas(QWidget):
    logout_requested = Signal()
    return_to_dashboard_requested = Signal()

    ARTICLE_SEARCH_URL = "https://www.abcp.ru/crossbase/api#articles_info"

    _MODES = {
        "exact": {
            "button": "Точные совпадения",
            "headers": ("Наименование", "Артикул", "Бренд", "Кол-во", "Ячейка"),
            "rows": (),
        },
        "stock": {
            "button": "Есть в МойСклад",
            "headers": ("Наименование", "Артикул", "Бренд", "Кол-во", "Ячейка"),
            "rows": (),
        },
        "analogs": {
            "button": "Аналоги",
            "headers": ("Наименование", "Бренд", "Артикул"),
            "rows": (),
        },
    }

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self._active_section = "paste"
        self._selected_mode = "exact"
        self._mode_buttons: dict[str, QPushButton] = {}
        self._section_buttons: dict[str, QPushButton] = {}
        self._parsed_analog_rows: list[tuple[str, str, str, str]] = []
        self._stock_rows: tuple[ProductStockMatch, ...] = ()
        self._stock_error_message = ""
        self._stock_lookup_in_progress = False
        self._stock_loader_thread: QThread | None = None
        self._stock_loader_worker: StockLookupWorker | None = None
        self._selected_brand = ""
        self._selected_warehouse_id = ""
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
            "4. Вернитесь сюда, выберите склад, вставьте текст страницы в большое поле и нажмите «Отправить»."
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

        warehouse_label = QLabel("Склад")
        warehouse_label.setObjectName("fieldLabel")
        panel_layout.addWidget(warehouse_label)

        self._warehouse_combo = QComboBox()
        self._warehouse_combo.setObjectName("brandFilterCombo")
        self._warehouse_combo.setCursor(Qt.PointingHandCursor)
        self._warehouse_combo.currentIndexChanged.connect(self._on_warehouse_changed)
        self._populate_warehouse_select()
        panel_layout.addWidget(self._warehouse_combo)

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
        self._status_label = QLabel("После отправки программа выделит аналоги и проверит наличие в МойСклад.")
        self._status_label.setObjectName("instructionText")
        self._status_label.setWordWrap(True)
        actions.addWidget(self._status_label, 1)

        self._submit_button = QPushButton("Отправить")
        self._submit_button.setObjectName("primaryAction")
        self._submit_button.setIcon(IconWidget.to_icon("send", "#061116", 16))
        self._submit_button.setIconSize(QSize(16, 16))
        self._submit_button.setCursor(Qt.PointingHandCursor)
        self._submit_button.setFixedSize(150, 42)
        self._submit_button.clicked.connect(self._submit_page_text)
        actions.addWidget(self._submit_button)
        self._refresh_submit_state()
        panel_layout.addLayout(actions)

        layout.addWidget(panel, 1)
        return page

    def _results_page(self) -> QFrame:
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._mode_switcher())
        self._brand_filter = self._brand_filter_panel()
        layout.addWidget(self._brand_filter)
        self._results_status_label = QLabel("")
        self._results_status_label.setObjectName("instructionText")
        self._results_status_label.setWordWrap(True)
        layout.addWidget(self._results_status_label)
        self._table = self._results_table()
        layout.addWidget(self._table, 1)
        return page

    def _brand_filter_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("brandFilterPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        label = QLabel("Бренд")
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        self._brand_filter_combo = QComboBox()
        self._brand_filter_combo.setObjectName("brandFilterCombo")
        self._brand_filter_combo.setCursor(Qt.PointingHandCursor)
        self._brand_filter_combo.currentIndexChanged.connect(self._on_brand_filter_changed)
        layout.addWidget(self._brand_filter_combo, 1)
        panel.setVisible(False)
        return panel

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

    def _populate_warehouse_select(self) -> None:
        self._warehouse_combo.blockSignals(True)
        self._warehouse_combo.clear()
        if self.session.warehouses:
            self._warehouse_combo.addItem("Выберите склад", "")
            for warehouse in sorted(self.session.warehouses, key=lambda item: item.name.casefold()):
                title = warehouse.name
                if warehouse.address:
                    title = f"{warehouse.name} - {warehouse.address}"
                self._warehouse_combo.addItem(title, warehouse.id)
            self._warehouse_combo.setCurrentIndex(0)
        else:
            self._warehouse_combo.addItem("Склады не загружены", "")
            self._warehouse_combo.setEnabled(False)
        self._selected_warehouse_id = ""
        self._warehouse_combo.blockSignals(False)

    def _on_warehouse_changed(self, *_args: object) -> None:
        self._selected_warehouse_id = self._warehouse_combo.currentData() or ""
        self._refresh_submit_state()

    def _refresh_submit_state(self) -> None:
        if not hasattr(self, "_submit_button"):
            return
        can_submit = bool(self._selected_warehouse_id) and not self._stock_lookup_in_progress
        self._submit_button.setEnabled(can_submit)
        self._submit_button.setCursor(Qt.PointingHandCursor if can_submit else Qt.ForbiddenCursor)
        if hasattr(self, "_warehouse_combo") and self.session.warehouses:
            self._warehouse_combo.setEnabled(not self._stock_lookup_in_progress)

    def _submit_page_text(self) -> None:
        print("[ArticleCheck] Submit clicked", flush=True)
        if not self._selected_warehouse_id:
            print("[ArticleCheck] Submit skipped: warehouse is not selected", flush=True)
            self._refresh_submit_state()
            return
        page_text = self._page_text.toPlainText()
        print(
            f"[ArticleCheck] Parsing pasted page: chars={len(page_text)}, warehouse_id={self._selected_warehouse_id}",
            flush=True,
        )
        self._parsed_analog_rows = self._parse_article_page(page_text)
        print(f"[ArticleCheck] Parsed ABCP rows: {len(self._parsed_analog_rows)}", flush=True)
        self._stock_rows = ()
        self._stock_error_message = ""
        self._selected_brand = ""
        self._populate_brand_filter()
        self._show_section("results")
        if not self._parsed_analog_rows:
            self._set_mode("stock")
            self._set_status("Не удалось найти JSON с артикулом и аналогами в скопированном тексте.")
            print("[ArticleCheck] Submit stopped: no ABCP JSON rows parsed", flush=True)
            return
        self._set_mode("stock")
        self._start_stock_lookup()

    def _start_stock_lookup(self) -> None:
        if self._stock_loader_thread is not None:
            print("[ArticleCheck] Stock lookup skipped: worker is already running", flush=True)
            return

        items = [ArticleLookupItem(brand=row[1], number=row[2], normalized_number=row[3]) for row in self._parsed_analog_rows]
        self._stock_lookup_in_progress = True
        self._set_status("Проверяем наличие в МойСклад...")
        self._submit_button.setText("Загрузка...")
        print(
            f"[ArticleCheck] Stock lookup started: items={len(items)}, warehouse_id={self._selected_warehouse_id}",
            flush=True,
        )
        self._refresh_submit_state()
        self._render_table()

        self._stock_loader_thread = QThread(self)
        self._stock_loader_worker = StockLookupWorker(self.session.access_token, self._selected_warehouse_id, items)
        self._stock_loader_worker.moveToThread(self._stock_loader_thread)
        self._stock_loader_thread.started.connect(self._stock_loader_worker.run)
        self._stock_loader_worker.succeeded.connect(self._apply_stock_rows)
        self._stock_loader_worker.failed.connect(self._handle_stock_error)
        self._stock_loader_worker.finished.connect(self._stock_loader_thread.quit)
        self._stock_loader_worker.finished.connect(self._stock_loader_worker.deleteLater)
        self._stock_loader_thread.finished.connect(self._stock_loader_thread.deleteLater)
        self._stock_loader_thread.finished.connect(self._clear_stock_loader)
        self._stock_loader_thread.start()

    def _apply_stock_rows(self, rows: object) -> None:
        self._stock_rows = tuple(row for row in rows if isinstance(row, ProductStockMatch)) if isinstance(rows, tuple) else ()
        self._stock_error_message = ""
        found_text = self._format_count(len(self._stock_rows), "товар", "товара", "товаров")
        self._set_status(f"Проверка завершена: найдено {found_text} в МойСклад.")
        print(f"[ArticleCheck] Stock rows applied: {len(self._stock_rows)}", flush=True)
        self._render_table()

    def _handle_stock_error(self, message: str) -> None:
        self._stock_rows = ()
        self._stock_error_message = message
        self._set_status(message)
        print(f"[ArticleCheck] Stock lookup error shown: {message}", flush=True)
        self._render_table()

    def _clear_stock_loader(self) -> None:
        self._stock_lookup_in_progress = False
        self._stock_loader_thread = None
        self._stock_loader_worker = None
        if hasattr(self, "_submit_button"):
            self._submit_button.setText("Отправить")
        self._refresh_submit_state()
        print("[ArticleCheck] Stock loader cleared", flush=True)
        self._render_table()

    def _set_status(self, message: str) -> None:
        if hasattr(self, "_status_label"):
            self._status_label.setText(message)
        if hasattr(self, "_results_status_label"):
            self._results_status_label.setText(message)

    def _set_mode(self, mode: str) -> None:
        self._selected_mode = mode
        for key, button in self._mode_buttons.items():
            button.setObjectName("modeToggleActive" if key == mode else "modeToggleInactive")
            button.style().unpolish(button)
            button.style().polish(button)
        self._refresh_brand_filter_visibility()
        self._render_table()

    def _render_table(self) -> None:
        if not hasattr(self, "_table"):
            return

        config = self._MODES[self._selected_mode]
        headers = config["headers"]
        if self._selected_mode == "analogs":
            headers = ("Тип", "Бренд", "Артикул", "Номер для поиска")
            rows = self._filtered_analog_rows()
        elif self._selected_mode == "stock":
            rows = self._stock_table_rows(self._stock_rows)
        elif self._selected_mode == "exact":
            exact_rows = tuple(row for row in self._stock_rows if row.brand_matches_query and row.quantity > 0)
            rows = self._stock_table_rows(exact_rows)
        else:
            rows = list(config["rows"])
        self._refresh_brand_filter_visibility()
        self._table.clear()
        self._table.clearSpans()
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        if self._stock_lookup_in_progress and self._selected_mode in ("exact", "stock"):
            self._render_loader_row(headers)
            return
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

    def _render_loader_row(self, headers: tuple[str, ...]) -> None:
        self._table.setRowCount(1)
        item = QTableWidgetItem("Загрузка данных из МойСклад...")
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setForeground(QColor(MINT))
        item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(0, 0, item)
        if len(headers) > 1:
            self._table.setSpan(0, 0, 1, len(headers))

    def _stock_table_rows(self, rows: tuple[ProductStockMatch, ...]) -> list[tuple[str, str, str, str, str]]:
        return [
            (row.name, row.article, row.brand, self._format_quantity(row.quantity), row.cell)
            for row in sorted(rows, key=lambda item: (item.brand.casefold(), item.article.casefold(), item.name.casefold()))
        ]

    @staticmethod
    def _format_quantity(quantity: float) -> str:
        numeric_quantity = float(quantity)
        if numeric_quantity.is_integer():
            return str(int(numeric_quantity))
        return f"{numeric_quantity:g}"

    @staticmethod
    def _format_count(count: int, one: str, few: str, many: str) -> str:
        if count % 10 == 1 and count % 100 != 11:
            word = one
        elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
            word = few
        else:
            word = many
        return f"{count} {word}"

    def _populate_brand_filter(self) -> None:
        if not hasattr(self, "_brand_filter_combo"):
            return

        brands = sorted(
            {row[1] for row in self._parsed_analog_rows if row[1]},
            key=str.casefold,
        )
        self._brand_filter_combo.blockSignals(True)
        self._brand_filter_combo.clear()
        self._brand_filter_combo.addItem("Все бренды", "")
        for brand in brands:
            self._brand_filter_combo.addItem(brand, brand)
        self._brand_filter_combo.setCurrentIndex(0)
        self._brand_filter_combo.blockSignals(False)
        self._refresh_brand_filter_visibility()

    def _on_brand_filter_changed(self, *_args: object) -> None:
        if not hasattr(self, "_brand_filter_combo"):
            return
        self._selected_brand = self._brand_filter_combo.currentData() or ""
        self._render_table()

    def _refresh_brand_filter_visibility(self) -> None:
        if not hasattr(self, "_brand_filter"):
            return
        self._brand_filter.setVisible(self._selected_mode == "analogs" and bool(self._parsed_analog_rows))

    def _filtered_analog_rows(self) -> list[tuple[str, str, str, str]]:
        rows = self._parsed_analog_rows
        if self._selected_brand:
            rows = [row for row in rows if row[1] == self._selected_brand]
        return sorted(rows, key=lambda row: (row[1].casefold(), row[2].casefold(), row[3].casefold()))

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

    def _parse_article_page(self, page_text: str) -> list[tuple[str, str, str, str]]:
        payload = self._extract_json_payload(page_text)
        if not isinstance(payload, dict):
            return []

        rows: list[tuple[str, str, str, str]] = []
        requested = self._article_row(payload, "Запрос", "outer_number")
        if requested:
            rows.append(requested)

        crosses = payload.get("crosses")
        if isinstance(crosses, list):
            for item in crosses:
                if not isinstance(item, dict):
                    continue
                analog = self._article_row(item, "Аналог", "numberFix")
                if analog:
                    rows.append(analog)

        return rows

    def _article_row(self, item: dict[str, Any], label: str, normalized_key: str) -> tuple[str, str, str, str] | None:
        brand = self._string_value(item.get("brand"))
        number = self._string_value(item.get("number"))
        normalized_number = self._string_value(item.get(normalized_key))
        if not brand and not number and not normalized_number:
            return None
        return (label, brand, number, normalized_number)

    def _string_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _extract_json_payload(self, page_text: str) -> dict[str, Any] | None:
        decoder = json.JSONDecoder()
        for index, character in enumerate(page_text):
            if character != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(page_text[index:])
            except JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return None

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
