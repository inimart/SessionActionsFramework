# framework_tool/main.py
# All comments and identifiers in English

import sys
from PySide6.QtWidgets import QApplication
from .gui.main_window import MainWindow # Relative import for main_window

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

if __name__ == '__main__':
    # This allows running the application directly by executing this main.py script
    # Ensure your terminal is in the 'hygiene_vr_framework' root directory
    # and your venv is active. Then run: python -m framework_tool.main
    # Or, if your PYTHONPATH is set up correctly to include the project root,
    # you might be able to run `python framework_tool/main.py`
    run_application()