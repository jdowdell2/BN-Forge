import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_menu_window import MainMenu



# set run configuration to this file
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    sys.exit(app.exec())



















