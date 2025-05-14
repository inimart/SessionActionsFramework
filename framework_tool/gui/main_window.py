# framework_tool/gui/main_window.py
# All comments and identifiers in English

import sys
import os
from typing import Optional, List, Callable # Aggiunto List per i type hint delle funzioni getter/setter

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel,
    QFileDialog, QMessageBox, QDialog # Aggiunto QDialog
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, Slot

# Import project data handling functions and classes
from ..project_io import json_handler
from ..data_models.project_data import ProjectData

# Import LabelEditorWidget
from .widgets.label_editor_widget import LabelEditorWidget # NUOVO IMPORT

class MainWindow(QMainWindow):
    """
    The main window for the SessionActions Framework tool.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.current_project_data: Optional[ProjectData] = None
        self.current_project_filepath: Optional[str] = None
        self.is_dirty: bool = False # To track unsaved changes

        self._init_ui()
        # _update_window_title() will be called by new_project()
        self.new_project() # Start with a fresh project

    def _init_ui(self):
        """Initializes the User Interface."""
        self.setWindowTitle("SessionActions Framework Tool") # Aggiornato nome
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget(self)
        self.layout = QVBoxLayout(central_widget)
        self.placeholder_label = QLabel("Welcome! Open or create a project to get started.", self)
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.placeholder_label)
        self.setCentralWidget(central_widget)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        # ... (azioni File Menu come prima) ...
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project_action)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project_action)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()

        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project_action)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_project_as_action)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- NUOVO: Manage Menu per gli editor di etichette ---
        manage_menu = menu_bar.addMenu("&Manage")

        edit_action_labels_action = QAction("Edit &ActionLabels...", self)
        edit_action_labels_action.triggered.connect(self.edit_action_labels)
        manage_menu.addAction(edit_action_labels_action)

        edit_item_labels_action = QAction("Edit &ItemLabels...", self)
        edit_item_labels_action.triggered.connect(self.edit_item_labels)
        manage_menu.addAction(edit_item_labels_action)

        edit_subaction_labels_action = QAction("Edit &SubActionLabels...", self)
        edit_subaction_labels_action.triggered.connect(self.edit_subaction_labels)
        manage_menu.addAction(edit_subaction_labels_action)
        
        # TODO: Aggiungere qui i menu per SubActionDefinitions, ActionDefinitions, SessionActions

        self.statusBar().showMessage("Ready")

    def _update_window_title(self):
        base_title = "SessionActions Framework Tool" # Aggiornato nome
        project_name_part = "Untitled"
        if self.current_project_filepath:
            project_name_part = os.path.basename(self.current_project_filepath)
        elif self.current_project_data and self.current_project_data.project_metadata.project_name not in [None, "New SessionActions Project", ""]: # Aggiornato nome default
            project_name_part = self.current_project_data.project_metadata.project_name
        
        dirty_marker = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{base_title} - {project_name_part}{dirty_marker}")

    def _check_unsaved_changes(self) -> bool:
        if not self.is_dirty:
            return True
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Do you want to save them before proceeding?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            return self.save_project_action()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def mark_dirty(self, dirty_status: bool = True):
        if self.is_dirty != dirty_status:
            self.is_dirty = dirty_status
            self._update_window_title()

    @Slot()
    def new_project_action(self):
        if not self._check_unsaved_changes():
            return
        self.new_project()
        self.statusBar().showMessage("New project created.", 5000)

    def new_project(self):
        self.current_project_data = json_handler.new_project(project_name="New SessionActions Project") # Aggiornato nome
        self.current_project_filepath = None
        self.mark_dirty(False)
        self._update_window_title()
        if self.current_project_data: # Check if current_project_data is not None
             self.placeholder_label.setText(f"New Project: {self.current_project_data.project_metadata.project_name}")
        else:
             self.placeholder_label.setText("Error: Could not initialize new project data.")
        print("New project initialized.")


    @Slot()
    def open_project_action(self):
        if not self._check_unsaved_changes():
            return
        start_dir = os.getcwd() 
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project File", start_dir, "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                self.current_project_data = json_handler.load_project(filepath)
                self.current_project_filepath = filepath
                self.mark_dirty(False) # Project is clean after loading
                self._update_window_title()
                self.statusBar().showMessage(f"Project '{os.path.basename(filepath)}' loaded.", 5000)
                if self.current_project_data: # Check if current_project_data is not None
                    self.placeholder_label.setText(f"Loaded Project: {self.current_project_data.project_metadata.project_name}")
                else:
                    self.placeholder_label.setText(f"Error: Could not load project data from {filepath}")

                print(f"Project loaded from: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading Project", f"Could not load project file:\n{filepath}\n\nError: {e}")
                self.statusBar().showMessage(f"Error loading project: {e}", 8000)

    @Slot()
    def save_project_action(self) -> bool:
        if not self.current_project_data:
            QMessageBox.warning(self, "No Project", "There is no project data to save.")
            return False
        if not self.current_project_filepath:
            return self.save_project_as_action()
        else:
            try:
                json_handler.save_project(self.current_project_data, self.current_project_filepath)
                self.mark_dirty(False) # Project is clean after saving
                # _update_window_title() is called by mark_dirty
                self.statusBar().showMessage(f"Project saved to '{self.current_project_filepath}'.", 5000)
                print(f"Project saved to: {self.current_project_filepath}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error Saving Project", f"Could not save project to file:\n{self.current_project_filepath}\n\nError: {e}")
                self.statusBar().showMessage(f"Error saving project: {e}", 8000)
                return False
    
    @Slot()
    def save_project_as_action(self) -> bool:
        if not self.current_project_data:
            QMessageBox.warning(self, "No Project", "There is no project data to save.")
            return False
        start_dir = os.path.dirname(self.current_project_filepath) if self.current_project_filepath else os.getcwd()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", start_dir, "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            self.current_project_filepath = filepath 
            return self.save_project_action() 
        return False

    # --- NUOVO: Metodi per aprire gli editor di etichette ---
    def _open_label_editor_dialog(self, title: str, 
                                 getter: Callable[[], List[str]], 
                                 setter: Callable[[List[str]], None]):
        """Helper function to create and show a dialog with LabelEditorWidget."""
        if not self.current_project_data:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400) # Give it some reasonable default size
        dialog.setMinimumHeight(300)

        layout = QVBoxLayout(dialog)
        editor_widget = LabelEditorWidget(
            widget_title=title, # Title for the widget itself, dialog has its own
            get_labels_func=getter,
            set_labels_func=setter,
            parent=dialog
        )
        editor_widget.labels_changed.connect(lambda: self.mark_dirty(True)) # Mark project dirty on changes
        
        layout.addWidget(editor_widget)
        dialog.setLayout(layout)
        
        dialog.exec() # Show as a modal dialog

    @Slot()
    def edit_action_labels(self):
        if self.current_project_data: # Ensure project data exists
            self._open_label_editor_dialog(
                title="Edit ActionLabels",
                getter=lambda: self.current_project_data.action_labels,
                setter=lambda lst: setattr(self.current_project_data, 'action_labels', lst)
            )

    @Slot()
    def edit_item_labels(self):
        if self.current_project_data:
            self._open_label_editor_dialog(
                title="Edit ItemLabels",
                getter=lambda: self.current_project_data.item_labels,
                setter=lambda lst: setattr(self.current_project_data, 'item_labels', lst)
            )

    @Slot()
    def edit_subaction_labels(self):
        if self.current_project_data:
            self._open_label_editor_dialog(
                title="Edit SubActionLabels",
                getter=lambda: self.current_project_data.sub_action_labels,
                setter=lambda lst: setattr(self.current_project_data, 'sub_action_labels', lst)
            )

    def closeEvent(self, event):
        if self._check_unsaved_changes():
            event.accept()
            print("Application closing.")
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("TestOrg")
    QApplication.setApplicationName("MainWindowTest - SessionActions") # Aggiornato nome
    
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())