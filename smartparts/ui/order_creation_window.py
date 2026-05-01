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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from smartparts.session import AppSession
from smartparts.theme import CYAN, MINT, RED
from smartparts.ui.icons import IconWidget
from smartparts.ui.styles import order_creation_stylesheet


class OrderCreationCanvas(QWidget):
    logout_requested = Signal()
    return_to_dashboard_requested = Signal()

    def __init__(self, session: AppSession) -> None:
        super().__init__()
        self.session = session
        self.setObjectName("orderCanvas")
        self.setStyleSheet(order_creation_stylesheet())

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
        layout.addWidget(self._nav_button("file-plus", "Новый документ", True))
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
        layout.addWidget(self._field_panel("Клиент из МойСклад", "ООО АвтоМаркет Север", "search"), 1)
        layout.addWidget(self._field_panel("Склад", "Основной", "warehouse", fixed_width=220), 0)
        layout.addWidget(self._field_panel("Предоплата", "15 000 ₽", None, fixed_width=150, bold=True), 0)
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
        for text, active in (("Заказ", True), ("Поставка", False)):
            button = QPushButton(text)
            button.setObjectName("toggleActive" if active else "toggleInactive")
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(34)
            row.addWidget(button, 1)
        layout.addLayout(row)
        return panel

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

        layout.addWidget(search, 1)
        layout.addWidget(add)
        return toolbar

    def _products_table(self) -> QTableWidget:
        table = QTableWidget(2, 8)
        table.setObjectName("productsTable")
        table.setHorizontalHeaderLabels(("Артикул", "Название", "Бренд", "Кол-во", "Закупка", "Продажа", "Сумма", ""))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for column, width in ((0, 86), (2, 76), (3, 58), (4, 78), (5, 78), (6, 84), (7, 42)):
            table.setColumnWidth(column, width)
        table.verticalHeader().setDefaultSectionSize(44)
        table.setAlternatingRowColors(False)

        rows = (
            ("OC650", "Фильтр масляный", "Knecht", "4", "620 ₽", "880 ₽", "3 520 ₽"),
            ("GDB1550", "Колодки тормозные", "TRW", "1", "3 900 ₽", "5 450 ₽", "5 450 ₽"),
        )
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                if column_index >= 3:
                    item.setTextAlignment(Qt.AlignCenter)
                if column_index == 6:
                    item.setForeground(QColor(MINT))
                elif column_index == 0:
                    item.setForeground(QColor("#F4FAFF"))
                else:
                    item.setForeground(QColor("#DDEAF2"))
                table.setItem(row_index, column_index, item)
            table.setCellWidget(row_index, 7, self._delete_row_button(table))
        return table

    @staticmethod
    def _delete_row_button(table: QTableWidget) -> QFrame:
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

        for label, value, accent in (
            ("Позиций", "12", False),
            ("Закупка", "280 400 ₽", False),
            ("Продажа", "341 900 ₽", True),
            ("Предоплата", "15 000 ₽", True),
        ):
            layout.addLayout(self._total_row(label, value, accent))

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
    def _total_row(label: str, value: str, accent: bool) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        label_widget = QLabel(label)
        label_widget.setObjectName("totalLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("totalValueAccent" if accent else "totalValue")
        row.addWidget(label_widget, 1)
        row.addWidget(value_widget)
        return row

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
        super().resizeEvent(event)
