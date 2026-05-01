from difflib import SequenceMatcher

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIntValidator, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT, RED
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import order_creation_stylesheet


class BrandOptionRow(QFrame):
    clicked = Signal()

    def __init__(self, text: str, icon: str, object_name: str, score: int | None = None) -> None:
        super().__init__()
        self.setObjectName(object_name)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46 if score is None else 42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)
        layout.addWidget(IconWidget(icon, MINT if object_name == "brandSuggestionActive" else CYAN if score is None else "#8FA8B9", 16))

        label = QLabel(text)
        label.setObjectName("brandSuggestionText")
        label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(label, 1)

        if score is not None:
            score_label = QLabel(f"{score}%")
            score_label.setObjectName("brandSuggestionScoreActive" if object_name == "brandSuggestionActive" else "brandSuggestionScore")
            layout.addWidget(score_label)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class BrandSelect(QWidget):
    text_changed = Signal(str)

    def __init__(self, brand_names: list[str], popup_parent: QWidget, value: str = "", *, show_label: bool = True, compact: bool = False) -> None:
        super().__init__()
        self._brand_names = sorted({name.strip() for name in brand_names if name.strip()})
        self._popup_parent = popup_parent
        self._committed_value = value
        self._is_applying_text = False
        self._has_pending_edit = False
        self._suggestions: list[tuple[str, int]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6 if show_label else 0)

        if show_label:
            label = QLabel("Бренд")
            label.setObjectName("fieldLabel")
            layout.addWidget(label)

        shell = QFrame()
        shell.setObjectName("brandSelectInput")
        shell.setFixedHeight(34 if compact else 42)
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(8 if compact else 12, 0, 8 if compact else 12, 0)
        shell_layout.setSpacing(6 if compact else 10)
        if not compact:
            shell_layout.addWidget(IconWidget("search", CYAN, 16))

        self._line_edit = QLineEdit(value)
        self._line_edit.setObjectName("brandSelectLineEdit")
        self._line_edit.setFrame(False)
        self._line_edit.setToolTip(value)
        if compact:
            self.setMinimumWidth(150)
            self._line_edit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._line_edit.installEventFilter(self)
        self._line_edit.textEdited.connect(self._handle_text_edited)
        shell_layout.addWidget(self._line_edit, 1)
        shell_layout.addWidget(IconWidget("chevron-down", "#8FA8B9", 14 if compact else 16))
        layout.addWidget(shell)

        self._dropdown = QFrame(popup_parent)
        self._dropdown.setObjectName("brandSelectDropdown")
        self._dropdown_layout = QVBoxLayout(self._dropdown)
        self._dropdown_layout.setContentsMargins(0, 0, 0, 0)
        self._dropdown_layout.setSpacing(0)
        self._dropdown.hide()

    def text(self) -> str:
        return self._line_edit.text()

    def setText(self, value: str) -> None:  # noqa: N802 - mirrors QLineEdit API
        self._is_applying_text = True
        self._line_edit.setText(value)
        self._line_edit.setToolTip(value)
        self._is_applying_text = False
        self.text_changed.emit(value)
        self._committed_value = value
        self._has_pending_edit = False
        self.hide_dropdown()

    def clear(self) -> None:
        self.setText("")

    def hide_dropdown(self) -> None:
        self._dropdown.hide()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API naming
        if watched is self._line_edit and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._accept_enter()
                return True
            if key == Qt.Key_Escape:
                self._reset_pending_edit()
                return True
        if watched is self._line_edit and event.type() == QEvent.FocusOut:
            QTimer.singleShot(120, self._reset_if_focus_left)
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        if self._dropdown.isVisible():
            self._position_dropdown()
        super().resizeEvent(event)

    def _handle_text_edited(self, query: str) -> None:
        if self._is_applying_text:
            return
        self._line_edit.setToolTip(query)
        self._has_pending_edit = True
        self._suggestions = self._closest_brands(query)
        self._render_dropdown(query)

    def _closest_brands(self, query: str) -> list[tuple[str, int]]:
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return []

        ranked: list[tuple[int, str]] = []
        for brand_name in self._brand_names:
            normalized_name = brand_name.casefold()
            if normalized_name == normalized_query:
                score = 100
            else:
                score = int(SequenceMatcher(None, normalized_query, normalized_name).ratio() * 100)
            if normalized_name.startswith(normalized_query) and normalized_name != normalized_query:
                score += 35
            elif normalized_query in normalized_name:
                score += 20
            ranked.append((100 if normalized_name == normalized_query else min(score, 99), brand_name))

        ranked.sort(key=lambda item: (-item[0], item[1].casefold()))
        return [(brand_name, score) for score, brand_name in ranked[:5]]

    def _render_dropdown(self, query: str) -> None:
        typed_value = query.strip()
        self._clear_dropdown_rows()
        if not typed_value:
            self._dropdown.hide()
            return

        for index, (brand_name, score) in enumerate(self._suggestions):
            self._dropdown_layout.addWidget(self._suggestion_button(brand_name, score, index == 0))

        if not self._has_exact_brand(typed_value):
            self._dropdown_layout.addWidget(self._create_button(typed_value))

        self._position_dropdown()
        self._dropdown.show()
        self._dropdown.raise_()

    def _suggestion_button(self, brand_name: str, score: int, active: bool) -> BrandOptionRow:
        row = BrandOptionRow(brand_name, "check" if active else "search", "brandSuggestionActive" if active else "brandSuggestion", score)
        row.clicked.connect(lambda: self._commit_value(brand_name))
        return row

    def _create_button(self, typed_value: str) -> BrandOptionRow:
        row = BrandOptionRow(f"Добавить новый бренд: \"{typed_value}\"", "plus", "brandCreateSuggestion")
        row.clicked.connect(lambda: self._commit_value(typed_value))
        return row

    def _accept_enter(self) -> None:
        typed_value = self._line_edit.text().strip()
        if not typed_value:
            self._reset_pending_edit()
            return
        if self._suggestions:
            self._commit_value(self._suggestions[0][0])
        else:
            self._commit_value(typed_value)

    def _commit_value(self, value: str) -> None:
        self._is_applying_text = True
        self._line_edit.setText(value)
        self._line_edit.setToolTip(value)
        self._is_applying_text = False
        self.text_changed.emit(value)
        self._committed_value = value
        self._has_pending_edit = False
        self._dropdown.hide()

    def _reset_if_focus_left(self) -> None:
        focus_widget = QApplication.focusWidget()
        if focus_widget is not None and self._is_dropdown_child(focus_widget):
            return
        if self._has_pending_edit:
            self._reset_pending_edit()

    def _reset_pending_edit(self) -> None:
        self._is_applying_text = True
        self._line_edit.setText(self._committed_value)
        self._line_edit.setToolTip(self._committed_value)
        self._is_applying_text = False
        self.text_changed.emit(self._committed_value)
        self._has_pending_edit = False
        self._dropdown.hide()

    def _has_exact_brand(self, value: str) -> bool:
        normalized_value = value.casefold()
        return any(brand_name.casefold() == normalized_value for brand_name in self._brand_names)

    def _position_dropdown(self) -> None:
        position = self.mapTo(self._popup_parent, QPoint(0, self.height() + 4))
        row_count = len(self._suggestions)
        has_create_row = bool(self._line_edit.text().strip()) and not self._has_exact_brand(self._line_edit.text().strip())
        height = (row_count * 42) + (46 if has_create_row else 0)
        self._dropdown.setGeometry(position.x(), position.y(), self.width(), height)

    def _clear_dropdown_rows(self) -> None:
        while self._dropdown_layout.count():
            item = self._dropdown_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _is_dropdown_child(self, widget: QWidget) -> bool:
        current: QWidget | None = widget
        while current is not None:
            if current is self._dropdown:
                return True
            current = current.parentWidget()
        return False


class OrderCreationCanvas(QWidget):
    logout_requested = Signal()
    return_to_dashboard_requested = Signal()

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self._brand_names = [brand.name for brand in self.session.brands]
        self._document_type_buttons: dict[str, QPushButton] = {}
        self._selected_document_type = "order"
        self._updating_table = False
        self._product_table_base_widths = {
            0: 106,
            1: 320,
            2: 176,
            3: 72,
            4: 96,
            5: 96,
            6: 104,
            7: 42,
        }
        self.setObjectName("orderCanvas")
        self.setStyleSheet(order_creation_stylesheet())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._sidebar_widget = self._sidebar()
        self._workspace_widget = self._workspace()
        root.addWidget(self._sidebar_widget)
        root.addWidget(self._workspace_widget, 1)

        self._product_overlay = self._product_add_overlay()
        self._product_overlay.setParent(self)
        self._product_overlay.hide()

    def _sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(244)

        layout = QVBoxLayout(sidebar)
        self._sidebar_layout = layout
        layout.setContentsMargins(22, 30, 22, 30)
        layout.setSpacing(24)
        layout.addWidget(self._brand_area())
        layout.addWidget(self._navigation())
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

        subtitle = QLabel("Создание заказа")
        subtitle.setObjectName("brandSubtitle")
        layout.addWidget(subtitle)
        return area

    def _navigation(self) -> QFrame:
        navigation = QFrame()
        layout = QVBoxLayout(navigation)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        new_document = self._nav_button("file-plus", "Новый документ", True)
        new_document.clicked.connect(self._reset_document)
        layout.addWidget(new_document)
        layout.addWidget(self._nav_button("history", "Черновики", False))
        layout.addWidget(self._nav_button("truck", "Поставщики", False))
        return navigation

    @staticmethod
    def _nav_button(icon: str, text: str, active: bool) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("navActive" if active else "navButton")
        button.setIcon(IconWidget.to_icon(icon, CYAN if active else "#8FA8B9", 18))
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(44 if active else 42)
        return button

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
        layout.addWidget(self._top_controls())
        layout.addWidget(self._content(), 1)
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

        title = QLabel("Новый заказ / поставка")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Выберите тип документа, клиента и склад, затем добавьте товары в таблицу")
        subtitle.setObjectName("pageSubtitle")
        self._page_subtitle = subtitle
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        back = QPushButton("На главную")
        back.setObjectName("backToDashboardButton")
        back.setIcon(IconWidget.to_icon("arrow-left", CYAN, 16))
        back.setIconSize(QSize(16, 16))
        back.setCursor(Qt.PointingHandCursor)
        back.setFixedHeight(38)
        back.clicked.connect(self.return_to_dashboard_requested.emit)

        reset = QPushButton("Новый документ")
        reset.setObjectName("newDocumentButton")
        reset.setIcon(IconWidget.to_icon("rotate-ccw", CYAN, 16))
        reset.setIconSize(QSize(16, 16))
        reset.setCursor(Qt.PointingHandCursor)
        reset.setFixedHeight(38)
        reset.clicked.connect(self._reset_document)

        layout.addWidget(text, 1)
        layout.addWidget(back)
        layout.addWidget(reset)
        return header

    def _top_controls(self) -> QFrame:
        controls = QFrame()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._document_type(), 0)
        client_panel, self._client_input = self._field_input_panel("Клиент из МойСклад", "ООО АвтоМаркет Север", "search")
        layout.addWidget(client_panel, 1)
        layout.addWidget(self._warehouse_panel(), 0)
        prepayment_panel, self._prepayment_input = self._field_input_panel("Предоплата", "", None, fixed_width=150, bold=True)
        self._prepayment_input.textChanged.connect(self._update_totals)
        layout.addWidget(prepayment_panel, 0)
        return controls

    def _document_type(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("formPanel")
        panel.setFixedWidth(170)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        label = QLabel("Тип")
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(6)
        for key, text, active in (("order", "Заказ", True), ("supply", "Поставка", False)):
            button = QPushButton(text)
            button.setObjectName("toggleActive" if active else "toggleInactive")
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(34)
            button.clicked.connect(lambda checked=False, document_type=key: self._set_document_type(document_type))
            self._document_type_buttons[key] = button
            row.addWidget(button, 1)
        layout.addLayout(row)
        return panel

    def _set_document_type(self, document_type: str) -> None:
        self._selected_document_type = document_type
        for key, button in self._document_type_buttons.items():
            button.setObjectName("toggleActive" if key == document_type else "toggleInactive")
            button.style().unpolish(button)
            button.style().polish(button)

    def _warehouse_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("formPanel")
        panel.setFixedWidth(220)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        label = QLabel("Склад")
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        select = QComboBox()
        self._warehouse_select = select
        select.setObjectName("comboBox")
        select.addItems(("Северный", "Давыдовский"))
        select.setFixedHeight(34)
        layout.addWidget(select)
        return panel

    def _field_input_panel(self, label_text: str, value: str, icon: str | None, fixed_width: int | None = None, bold: bool = False) -> tuple[QFrame, QLineEdit]:
        panel = QFrame()
        panel.setObjectName("formPanel")
        if fixed_width is not None:
            panel.setFixedWidth(fixed_width)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        shell = QFrame()
        shell.setObjectName("inputShell")
        shell.setFixedHeight(34)
        row = QHBoxLayout(shell)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)
        if icon is not None:
            row.addWidget(IconWidget(icon, CYAN if icon == "warehouse" else "#8FA8B9", 16))
        field = QLineEdit(value)
        field.setObjectName("lineEdit")
        field.setFrame(False)
        if bold:
            field.setProperty("accentText", True)
        row.addWidget(field, 1)
        layout.addWidget(shell)
        return panel, field

    @staticmethod
    def _field_panel(label_text: str, value: str, icon: str | None, fixed_width: int | None = None, bold: bool = False) -> QFrame:
        panel = QFrame()
        panel.setObjectName("formPanel")
        if fixed_width is not None:
            panel.setFixedWidth(fixed_width)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        shell = QFrame()
        shell.setObjectName("inputShell")
        shell.setFixedHeight(34)
        row = QHBoxLayout(shell)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)
        if icon is not None:
            row.addWidget(IconWidget(icon, CYAN if icon == "warehouse" else "#8FA8B9", 16))
        text = QLabel(value)
        text.setObjectName("totalValue" if bold else "operatorText")
        row.addWidget(text, 1)
        layout.addWidget(shell)
        return panel

    def _content(self) -> QFrame:
        content = QFrame()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._products_panel(), 1)
        self._totals_panel_widget = self._totals_panel()
        layout.addWidget(self._totals_panel_widget)
        self._update_totals()
        return content

    def _products_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("productsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._table_toolbar())
        layout.addWidget(self._products_table(), 1)
        return panel

    def _table_toolbar(self) -> QFrame:
        toolbar = QFrame()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        search = QFrame()
        search.setObjectName("searchShell")
        search.setFixedHeight(40)
        search_layout = QHBoxLayout(search)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)
        search_layout.addWidget(IconWidget("search", CYAN, 16))
        field = QLineEdit()
        field.setObjectName("lineEdit")
        field.setPlaceholderText("Артикул, название или штрихкод")
        field.setFrame(False)
        search_layout.addWidget(field, 1)

        add = QPushButton("Добавить")
        add.setObjectName("primaryAction")
        add.setIcon(IconWidget.to_icon("plus", "#061116", 16))
        add.setIconSize(QSize(16, 16))
        add.setCursor(Qt.PointingHandCursor)
        add.setFixedSize(136, 40)
        add.clicked.connect(self._show_product_overlay)

        layout.addWidget(search, 1)
        layout.addWidget(add)
        return toolbar

    def _products_table(self) -> QTableWidget:
        table = QTableWidget(2, 8)
        self._products_table_widget = table
        table.setObjectName("productsTable")
        table.setHorizontalHeaderLabels(("Артикул", "Название", "Бренд", "Кол-во", "Закупка", "Продажа", "Сумма", ""))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setWordWrap(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        for column, width in self._product_table_base_widths.items():
            table.setColumnWidth(column, width)
        table.verticalHeader().setDefaultSectionSize(58)
        table.setAlternatingRowColors(False)

        rows = (
            ("OC650", "Фильтр масляный", "Knecht", "4", "620 ₽", "880 ₽", "3 520 ₽"),
            ("GDB1550", "Колодки тормозные", "TRW", "1", "3 900 ₽", "5 450 ₽", "5 450 ₽"),
        )
        for row_index, row in enumerate(rows):
            self._fill_table_row(row_index, row[:6])
        table.itemChanged.connect(self._handle_table_item_changed)
        self._update_totals()
        QTimer.singleShot(0, self._resize_product_table_columns)
        return table

    def _resize_product_table_columns(self) -> None:
        if not hasattr(self, "_products_table_widget"):
            return
        table = self._products_table_widget
        available_width = table.viewport().width()
        base_total = sum(self._product_table_base_widths.values())
        extra_width = max(0, available_width - base_total)

        name_extra = int(extra_width * 0.68)
        brand_extra = extra_width - name_extra
        for column, width in self._product_table_base_widths.items():
            if column == 1:
                width += name_extra
            elif column == 2:
                width += brand_extra
            table.setColumnWidth(column, width)

    def _product_add_overlay(self) -> QFrame:
        overlay = QFrame(self)
        overlay.setObjectName("productOverlay")

        outer = QVBoxLayout(overlay)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(0)
        outer.addStretch(1)

        center = QHBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.addStretch(1)

        window = QFrame()
        self._product_add_window = window
        window.setObjectName("productAddWindow")
        window.setMinimumSize(760, 500)
        window.setMaximumSize(1060, 660)

        layout = QVBoxLayout(window)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        layout.addWidget(self._product_add_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(16)
        body.addWidget(self._product_search_panel(), 1)
        body.addWidget(self._product_edit_panel(), 0)
        layout.addLayout(body, 1)

        center.addWidget(window)
        center.addStretch(1)
        outer.addLayout(center)
        outer.addStretch(1)
        return overlay

    def _product_add_header(self) -> QFrame:
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        text = QFrame()
        text_layout = QVBoxLayout(text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        title = QLabel("Добавить товар")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Найдите товар по артикулу, названию или штрихкоду и заполните данные для таблицы")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        close = QPushButton("Вернуться к заказу")
        close.setObjectName("secondaryAction")
        close.setIcon(IconWidget.to_icon("arrow-left", CYAN, 16))
        close.setIconSize(QSize(20, 20))
        close.setCursor(Qt.PointingHandCursor)
        close.setFixedHeight(38)
        close.setMinimumWidth(220)
        close.clicked.connect(self._hide_product_overlay)

        layout.addWidget(text, 1)
        layout.addWidget(close)
        return header

    def _product_search_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("productAddPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        shell = QFrame()
        shell.setObjectName("productSearchShell")
        shell.setFixedHeight(46)
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(14, 0, 14, 0)
        shell_layout.setSpacing(8)
        shell_layout.addWidget(IconWidget("scan-line", CYAN, 18))

        search = QLineEdit()
        self._product_search_input = search
        search.setObjectName("lineEdit")
        search.setPlaceholderText("Артикул, название или штрихкод")
        search.setFrame(False)
        search.returnPressed.connect(self._fill_product_from_search)
        shell_layout.addWidget(search, 1)

        enter = QLabel("Enter")
        enter.setObjectName("mutedText")
        shell_layout.addWidget(enter)
        layout.addWidget(shell)

        found = QLabel("Найдено в справочнике")
        found.setObjectName("sectionAccentTitle")
        layout.addWidget(found)

        layout.addWidget(
            self._product_result_button(
                "OC90 · Фильтр масляный\nKnecht / Mahle · остаток 2 шт · аналогов 6      890 ₽",
                ("OC90", "Фильтр масляный", "Knecht", "4", "620 ₽", "890 ₽"),
                True,
            )
        )
        layout.addWidget(
            self._product_result_button(
                "OC90OF · Фильтр масляный\nFiltron · под заказ · доставка 2 дня              760 ₽",
                ("OC90OF", "Фильтр масляный", "Filtron", "1", "540 ₽", "760 ₽"),
                False,
            )
        )

        hint = QFrame()
        hint.setObjectName("scannerHint")
        hint_layout = QVBoxLayout(hint)
        hint_layout.setAlignment(Qt.AlignCenter)
        hint_layout.setContentsMargins(16, 16, 16, 16)
        hint_layout.setSpacing(8)
        hint_layout.addWidget(IconWidget("barcode", "#8FA8B9", 28), 0, Qt.AlignCenter)
        hint_text = QLabel("Сканер сразу подставит найденный товар в форму справа")
        hint_text.setObjectName("hintText")
        hint_text.setAlignment(Qt.AlignCenter)
        hint_text.setWordWrap(True)
        hint_layout.addWidget(hint_text)
        layout.addWidget(hint, 1)
        return panel

    def _product_result_button(self, text: str, data: tuple[str, str, str, str, str, str], active: bool) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("productResultActive" if active else "productResult")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(62)
        button.setIcon(IconWidget.to_icon("package-search", CYAN if active else "#8FA8B9", 17))
        button.setIconSize(QSize(17, 17))
        button.clicked.connect(lambda: self._populate_product_form(data))
        return button

    def _product_edit_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("productAddPanel")
        panel.setFixedWidth(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Данные товара")
        title.setObjectName("panelTitle")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        form = QFrame()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        self._article_input = self._product_input(form_layout, "Артикул", "", bold=True)
        self._name_input = self._product_input(form_layout, "Наименование", "")

        brand_qty = QHBoxLayout()
        brand_qty.setSpacing(10)
        brand_names = [brand.name for brand in self.session.brands]
        self._brand_input = BrandSelect(brand_names, self, "")
        brand_qty.addWidget(self._brand_input, 1)
        self._qty_input = self._product_input(brand_qty, "Количество", "", accent=True, fixed_width=92)
        self._qty_input.setValidator(QIntValidator(1, 9999, self))
        form_layout.addLayout(brand_qty)

        prices = QHBoxLayout()
        prices.setSpacing(10)
        self._purchase_input = self._product_input(prices, "Цена закупки", "")
        self._sale_input = self._product_input(prices, "Цена продажи", "", accent_text=True)
        form_layout.addLayout(prices)

        self._comment_input = self._product_input(form_layout, "Примечание", "")
        layout.addWidget(form)
        layout.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        add = QPushButton("Добавить в заказ")
        self._add_product_button = add
        add.setObjectName("productSecondaryAction")
        add.setIcon(IconWidget.to_icon("check", CYAN, 16))
        add.setIconSize(QSize(16, 16))
        add.setCursor(Qt.PointingHandCursor)
        add.setFixedHeight(46)
        add.clicked.connect(lambda: self._add_product_to_order(False))

        add_more = QPushButton("Добавить и еще товар")
        self._add_more_product_button = add_more
        add_more.setObjectName("primaryAction")
        add_more.setIcon(IconWidget.to_icon("plus", "#061116", 16))
        add_more.setIconSize(QSize(16, 16))
        add_more.setCursor(Qt.PointingHandCursor)
        add_more.setFixedHeight(46)
        add_more.clicked.connect(lambda: self._add_product_to_order(True))

        actions.addWidget(add, 1)
        actions.addWidget(add_more, 1)
        layout.addLayout(actions)
        self._connect_product_validation()
        self._update_product_actions()
        return panel

    def _product_input(
        self,
        parent_layout: QVBoxLayout | QHBoxLayout,
        label_text: str,
        value: str,
        *,
        bold: bool = False,
        accent: bool = False,
        accent_text: bool = False,
        fixed_width: int | None = None,
    ) -> QLineEdit:
        group = QFrame()
        if fixed_width is not None:
            group.setFixedWidth(fixed_width)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

        field = QLineEdit(value)
        field.setObjectName("productInputAccent" if accent else "productInput")
        if bold:
            field.setProperty("strongText", True)
        if accent_text:
            field.setProperty("accentText", True)
        field.setFrame(False)
        field.setFixedHeight(38)
        field.setAlignment(Qt.AlignCenter)
        layout.addWidget(field)
        parent_layout.addWidget(group, 1)
        return field

    def _show_product_overlay(self) -> None:
        self._reset_product_form()
        self._position_product_overlay()
        self._product_overlay.show()
        self._product_overlay.raise_()
        self._product_search_input.setFocus()
        self._product_search_input.selectAll()

    def _hide_product_overlay(self) -> None:
        self._brand_input.hide_dropdown()
        self._product_overlay.hide()

    def _fill_product_from_search(self) -> None:
        query = self._product_search_input.text().strip().upper()
        if "OF" in query:
            self._populate_product_form(("OC90OF", "Фильтр масляный", "Filtron", "1", "540 ₽", "760 ₽"))
        else:
            self._populate_product_form(("OC90", "Фильтр масляный", "Knecht", "4", "620 ₽", "890 ₽"))

    def _populate_product_form(self, data: tuple[str, str, str, str, str, str]) -> None:
        article, name, brand, quantity, purchase, sale = data
        self._article_input.setText(article)
        self._name_input.setText(name)
        self._brand_input.setText(brand)
        self._qty_input.setText(quantity)
        self._purchase_input.setText(purchase)
        self._sale_input.setText(sale)

    def _add_product_to_order(self, keep_open: bool) -> None:
        if not self._product_form_is_valid():
            return

        table = self._products_table_widget
        row_index = table.rowCount()
        table.insertRow(row_index)

        quantity = int(self._qty_input.text())
        values = (
            self._article_input.text().strip(),
            self._name_input.text().strip(),
            self._brand_input.text().strip(),
            str(quantity),
            self._purchase_input.text().strip(),
            self._sale_input.text().strip(),
        )
        self._fill_table_row(row_index, values)
        self._update_totals()

        if keep_open:
            self._reset_product_form()
            self._position_product_overlay()
            self._product_overlay.show()
            self._product_overlay.raise_()
            self._product_search_input.setFocus()
        else:
            self._hide_product_overlay()

    def _product_form_is_valid(self) -> bool:
        required_fields = (
            self._article_input,
            self._name_input,
            self._brand_input,
            self._qty_input,
            self._purchase_input,
            self._sale_input,
        )
        return all(field.text().strip() for field in required_fields)

    def _connect_product_validation(self) -> None:
        for field in (self._article_input, self._name_input, self._qty_input, self._purchase_input, self._sale_input):
            field.textChanged.connect(self._update_product_actions)
        self._brand_input.text_changed.connect(self._update_product_actions)

    def _update_product_actions(self) -> None:
        enabled = self._product_form_is_valid()
        self._add_product_button.setEnabled(enabled)
        self._add_more_product_button.setEnabled(enabled)

    def _reset_product_form(self) -> None:
        self._product_search_input.clear()
        self._populate_product_form(("", "", "", "", "", ""))
        self._comment_input.clear()
        self._update_product_actions()

    def _fill_table_row(self, row_index: int, values: tuple[str, str, str, str, str, str]) -> None:
        table = self._products_table_widget
        self._updating_table = True
        article, name, brand, quantity, purchase, sale = values
        for column_index, value in enumerate((article, name, quantity, purchase, sale)):
            table_column = column_index if column_index < 2 else column_index + 1
            table.setItem(row_index, table_column, self._table_item(value, table_column))

        brand_select = BrandSelect(self._brand_names, self, brand, show_label=False, compact=True)
        brand_select.text_changed.connect(self._update_totals)
        table.setCellWidget(row_index, 2, brand_select)
        table.setItem(row_index, 6, self._table_item("", 6))
        table.setCellWidget(row_index, 7, self._delete_row_button(table, self._update_totals))
        self._updating_table = False
        self._recalculate_row_total(row_index)

    @staticmethod
    def _table_item(value: str, column_index: int) -> QTableWidgetItem:
        item = QTableWidgetItem(value)
        item.setToolTip(value)
        if column_index >= 3:
            item.setTextAlignment(Qt.AlignCenter)
        elif column_index == 1:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if column_index == 6:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setForeground(QColor(MINT))
        elif column_index == 0:
            item.setForeground(QColor("#F4FAFF"))
        else:
            item.setForeground(QColor("#DDEAF2"))
        return item

    def _handle_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table:
            return
        item.setToolTip(item.text())
        if item.column() in (3, 5):
            self._recalculate_row_total(item.row())
        self._update_totals()

    def _recalculate_row_total(self, row_index: int) -> None:
        table = self._products_table_widget
        quantity_item = table.item(row_index, 3)
        sale_item = table.item(row_index, 5)
        quantity = self._rubles_to_int(quantity_item.text() if quantity_item is not None else "")
        sale_price = self._rubles_to_int(sale_item.text() if sale_item is not None else "")
        self._updating_table = True
        total_item = table.item(row_index, 6)
        if total_item is None:
            total_item = self._table_item("", 6)
            table.setItem(row_index, 6, total_item)
        total_text = self._format_rubles(quantity * sale_price)
        total_item.setText(total_text)
        total_item.setToolTip(total_text)
        self._updating_table = False
        self._update_totals()

    def _reset_document(self) -> None:
        self._products_table_widget.setRowCount(0)
        self._client_input.clear()
        self._prepayment_input.clear()
        self._set_document_type("order")
        self._warehouse_select.setCurrentIndex(0)
        self._update_totals()

    def _update_totals(self) -> None:
        if not hasattr(self, "_products_table_widget") or not hasattr(self, "_total_positions_value"):
            return
        purchase_total = 0
        sale_total = 0
        for row in range(self._products_table_widget.rowCount()):
            quantity_item = self._products_table_widget.item(row, 3)
            purchase_item = self._products_table_widget.item(row, 4)
            sale_item = self._products_table_widget.item(row, 5)
            quantity = self._rubles_to_int(quantity_item.text() if quantity_item is not None else "")
            purchase_total += quantity * self._rubles_to_int(purchase_item.text() if purchase_item is not None else "")
            sale_total += quantity * self._rubles_to_int(sale_item.text() if sale_item is not None else "")

        self._total_positions_value.setText(str(self._products_table_widget.rowCount()))
        self._total_purchase_value.setText(self._format_rubles(purchase_total))
        self._total_sale_value.setText(self._format_rubles(sale_total))
        self._total_prepayment_value.setText(self._format_rubles(self._rubles_to_int(self._prepayment_input.text())))

    @staticmethod
    def _rubles_to_int(value: str) -> int:
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits or "0")

    @staticmethod
    def _format_rubles(value: int) -> str:
        return f"{value:,}".replace(",", " ") + " ₽"

    def _position_product_overlay(self) -> None:
        self._product_overlay.setGeometry(self.rect())
        width = max(760, min(self.width() - 80, 1060))
        height = max(500, min(self.height() - 64, 660))
        self._product_add_window.setFixedSize(width, height)

    @staticmethod
    def _delete_row_button(table: QTableWidget, after_remove: object | None = None) -> QFrame:
        holder = QFrame()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        button = QPushButton()
        button.setObjectName("deleteRowButton")
        button.setIcon(IconWidget.to_icon("x", "#FF7A85", 14))
        button.setIconSize(QSize(14, 14))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedSize(22, 22)

        def remove_row() -> None:
            for row in range(table.rowCount()):
                if table.cellWidget(row, 7) is holder:
                    table.removeRow(row)
                    if callable(after_remove):
                        after_remove()
                    break

        button.clicked.connect(remove_row)
        layout.addWidget(button)
        return holder

    def _totals_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("totalsPanel")
        panel.setFixedWidth(230)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Итоги")
        title.setObjectName("panelTitle")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        total_rows = (
            ("positions", "Позиций", "0", False),
            ("purchase", "Закупка", "0 ₽", False),
            ("sale", "Продажа", "0 ₽", True),
            ("prepayment", "Предоплата", "0 ₽", True),
        )
        for key, label, value, accent in total_rows:
            row, value_widget = self._total_row(label, value, accent)
            setattr(self, f"_total_{key}_value", value_widget)
            layout.addLayout(row)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #263948;")
        layout.addWidget(divider)

        confirm = QPushButton("Отправить в МойСклад")
        confirm.setObjectName("primaryAction")
        confirm.setIcon(IconWidget.to_icon("send", "#061116", 16))
        confirm.setIconSize(QSize(16, 16))
        confirm.setCursor(Qt.PointingHandCursor)
        confirm.setFixedHeight(46)
        layout.addWidget(confirm)

        save = QPushButton("Сохранить черновик")
        save.setObjectName("secondaryAction")
        save.setIcon(IconWidget.to_icon("file-plus", CYAN, 16))
        save.setIconSize(QSize(16, 16))
        save.setCursor(Qt.PointingHandCursor)
        save.setFixedHeight(42)
        layout.addWidget(save)

        hint = QFrame()
        hint.setObjectName("hintBox")
        hint_layout = QVBoxLayout(hint)
        hint_layout.setContentsMargins(12, 12, 12, 12)
        hint_layout.setSpacing(8)
        hint_title = QLabel("После подтверждения")
        hint_title.setObjectName("hintTitle")
        hint_text = QLabel("Откроется распределение товаров по заказам поставщикам с датами доставки.")
        hint_text.setObjectName("hintText")
        hint_text.setWordWrap(True)
        hint_layout.addWidget(hint_title)
        hint_layout.addWidget(hint_text)
        layout.addWidget(hint)
        layout.addStretch(1)
        return panel

    @staticmethod
    def _total_row(label: str, value: str, accent: bool) -> tuple[QHBoxLayout, QLabel]:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        label_widget = QLabel(label)
        label_widget.setObjectName("totalLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("totalValueAccent" if accent else "totalValue")
        row.addWidget(label_widget, 1)
        row.addWidget(value_widget)
        return row, value_widget

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
        narrow = width < 1040
        self._totals_panel_widget.setVisible(not narrow)
        self._sidebar_widget.setVisible(not compact)
        self._page_subtitle.setVisible(width >= 900)
        margin = 24 if compact else 34
        self._workspace_layout.setContentsMargins(margin, 24 if compact else 28, margin, 24 if compact else 28)
        if self._product_overlay.isVisible():
            self._position_product_overlay()
        super().resizeEvent(event)
        QTimer.singleShot(0, self._resize_product_table_columns)
