# framework_tool/main.py
# All comments and identifiers in English

import sys
from PySide6.QtWidgets import QApplication
from framework_tool.gui.main_window import MainWindow

def run_application():
    """
    Initializes and runs the Qt application.
    """
    app = QApplication(sys.argv)
    
    # Set application name and organization for QSettings (optional but good practice)
    # This will be used by QFileDialog to remember last opened/saved directories, etc.
    QApplication.setOrganizationName("Inimart") # Change as needed
    QApplication.setApplicationName("SessionActions Framework Tool")

    main_win = MainWindow()
    main_win.show()
    
    sys.exit(app.exec())

def main():
    """Main entry point for the application"""
    run_application()

if __name__ == '__main__':
    main()