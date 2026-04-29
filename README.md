# SmartParts

Локальное desktop-приложение для учета автозапчастей и работы оператора магазина.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Структура проекта

```text
SmartParts/
├── main.py                  # тонкая точка входа
├── requirements.txt         # зависимости проекта
└── smartparts/
    ├── app.py               # создание QApplication и главного окна
    ├── theme.py             # общие цвета и размеры
    └── ui/
        ├── icons.py         # рисуемые Qt-иконки
        ├── login_window.py  # окно и экран входа
        └── styles.py        # стили экрана входа
```

## Принципы

- UI разделен по ответственностям: окно, стили, тема и иконки находятся в отдельных модулях.
- Точка входа `main.py` не содержит бизнес-логики и только запускает приложение.
- Общие значения вынесены в `smartparts/theme.py`, чтобы новые экраны использовали единый визуальный язык.
