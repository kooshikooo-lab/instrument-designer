APP_STYLESHEET = """
QMainWindow {
    background-color: #1a1a1a;
}
QWidget {
    background-color: #1a1a1a;
    color: #D4C8B8;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #3a3028;
    border-radius: 10px;
    margin-top: 16px;
    padding: 18px 14px 14px 14px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #222222, stop:1 #1e1e1e);
    color: #D4C8B8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    color: #C99B5C;
    letter-spacing: 0.5px;
    background-color: #1a1a1a;
}
QTabWidget::pane {
    border: 1px solid #3a3028;
    border-radius: 8px;
    background-color: #1a1a1a;
    top: -1px;
}
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2a2a2a, stop:1 #222222);
    color: #A09080;
    border: 1px solid #3a3028;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 10px 24px;
    margin-right: 2px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8B5E3C, stop:1 #7A4E2C);
    color: #ffffff;
    border-color: #8B5E3C;
}
QTabBar::tab:hover:!selected {
    background: #333333;
    color: #D4C8B8;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8B5E3C, stop:1 #7A4E2C);
    color: #ffffff;
    border: 1px solid #A07050;
    border-radius: 6px;
    padding: 8px 22px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #A07050, stop:1 #8B5E3C);
    border-color: #C09070;
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6B4E2C, stop:1 #5A3E1C);
}
QPushButton:disabled {
    background: #333333;
    color: #666666;
    border-color: #444444;
}
QComboBox {
    background-color: #252525;
    color: #D4C8B8;
    border: 1px solid #3a3028;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 24px;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #8B5E3C;
}
QComboBox:focus {
    border-color: #C99B5C;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #C99B5C;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #252525;
    color: #D4C8B8;
    selection-background-color: #8B5E3C;
    selection-color: #ffffff;
    border: 1px solid #3a3028;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}
QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    color: #D4C8B8;
    border: 1px solid #3a3028;
    border-radius: 6px;
    padding: 6px 8px;
    min-height: 22px;
    font-size: 12px;
}
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #8B5E3C;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #C99B5C;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    border-left: 1px solid #3a3028;
    border-bottom: 1px solid #3a3028;
    border-top-right-radius: 5px;
    background-color: #333;
    width: 22px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    border-left: 1px solid #3a3028;
    border-bottom-right-radius: 5px;
    background-color: #333;
    width: 22px;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #C99B5C;
    margin-top: 4px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #C99B5C;
    margin-bottom: 4px;
}
QTextEdit {
    background-color: #141414;
    color: #C8C0B0;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
    selection-background-color: #8B5E3C;
}
QLabel {
    color: #D4C8B8;
    background: transparent;
}
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e1e, stop:1 #181818);
    color: #D4C8B8;
    border-top: 1px solid #2a2a2a;
    font-size: 11px;
    min-height: 24px;
}
QMenuBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #222222, stop:1 #1a1a1a);
    color: #D4C8B8;
    border-bottom: 1px solid #2a2a2a;
    padding: 2px 0;
    font-size: 12px;
}
QMenuBar::item {
    padding: 6px 14px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #8B5E3C;
    color: #ffffff;
}
QMenu {
    background-color: #222222;
    color: #D4C8B8;
    border: 1px solid #3a3028;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #8B5E3C;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #3a3028;
    margin: 6px 10px;
}
QProgressBar {
    border: 1px solid #3a3028;
    border-radius: 5px;
    text-align: center;
    color: #E8D5B7;
    background-color: #1a1a1a;
    min-height: 20px;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #C99B5C, stop:1 #8B5E3C);
    border-radius: 4px;
}
QSplitter::handle {
    background-color: #2a2a2a;
    width: 2px;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}
QCheckBox {
    color: #D4C8B8;
    spacing: 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
}
QCheckBox::indicator:unchecked {
    border: 2px solid #4a3a2a;
    background-color: #222;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8B5E3C, stop:1 #7A4E2C);
    border: 2px solid #A07050;
}
QCheckBox::indicator:hover {
    border-color: #C99B5C;
}
QScrollBar:vertical {
    background: #141414;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3a3028;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #8B5E3C;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #141414;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #3a3028;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #8B5E3C;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    outline: none;
    font-size: 12px;
}
QListWidget::item {
    padding: 12px 14px;
    border-bottom: 1px solid #242424;
    color: #D4C8B8;
    border-radius: 4px;
    margin: 1px 4px;
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8B5E3C, stop:1 #7A4E2C);
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #2a2a2a;
}
QLineEdit {
    background-color: #252525;
    color: #D4C8B8;
    border: 1px solid #3a3028;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    selection-background-color: #8B5E3C;
}
QLineEdit:focus {
    border-color: #C99B5C;
}
QDialog {
    background-color: #1a1a1a;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
}
"""
