import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui_main_window import MainWindow

dark_stylesheet = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 2px solid #89b4fa;
    border-radius: 8px;
    margin-top: 1ex;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
}
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 16px;
    color: #cdd6f4;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #89b4fa;
    color: #11111b;
}
QPushButton:pressed {
    background-color: #74c7ec;
    color: #11111b;
}
QPushButton:checked {
    background-color: #a6e3a1;
    color: #11111b;
}
QComboBox, QDoubleSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
    color: #cdd6f4;
}
QComboBox:drop-down {
    border: 0px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}
QSlider::groove:horizontal {
    border: 1px solid #45475a;
    height: 8px;
    background: #313244;
    margin: 2px 0;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #89b4fa;
    border: 1px solid #89b4fa;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QLabel {
    color: #cdd6f4;
    background-color: transparent;
}
QStatusBar {
    background-color: #11111b;
    color: #a6e3a1;
    font-weight: bold;
}
"""

def main():
    app = QApplication(sys.argv)
    
    # Set a modern style and stylesheet
    app.setStyle("Fusion")
    app.setStyleSheet(dark_stylesheet)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
