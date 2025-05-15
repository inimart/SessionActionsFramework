# framework_tool/gui/main_window.py
# All comments and identifiers in English

import sys
import os
from typing import Optional, List, Callable 

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel,
    QFileDialog, QMessageBox, QDialog, QSplitter 
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, Slot

from ..project_io import json_handler
from ..data_models.project_data import ProjectData
# from ..data_models.sub_action_definition import SubActionDefinition # Not directly used here
# from ..data_models.action_definition import ActionDefinition # Not directly used here
# from ..data_models.session_graph import SessionActionsGraph # Not directly used here

from .widgets.label_editor_widget import LabelEditorWidget
from .dialogs.manage_sub_action_definitions_dialog import ManageSubActionDefinitionsDialog
from .dialogs.manage_action_definitions_dialog import ManageActionDefinitionsDialog
from .dialogs.manage_session_actions_dialog import ManageSessionActionsDialog


class MainWindow(QMainWindow):
    """
    The main window for the SessionActions Framework tool.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_project_data: Optional[ProjectData] = None
        self.current_project_filepath: Optional[str] = None
        self.is_dirty: bool = False
        self._init_ui()
        self.new_project()

    def _init_ui(self):
        self.setWindowTitle("SessionActions Framework Tool")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget(self)
        self.main_layout = QVBoxLayout(central_widget) 
        self.placeholder_label = QLabel("Welcome! Open or create a project.\nUse 'Manage' menu to edit definitions and session flows.", self)
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.placeholder_label)
        self.setCentralWidget(central_widget)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        new_action = QAction("&New Project", self); new_action.setShortcut(QKeySequence.StandardKey.New); new_action.triggered.connect(self.new_project_action); file_menu.addAction(new_action)
        open_action = QAction("&Open Project...", self); open_action.setShortcut(QKeySequence.StandardKey.Open); open_action.triggered.connect(self.open_project_action); file_menu.addAction(open_action)
        file_menu.addSeparator()
        save_action = QAction("&Save Project", self); save_action.setShortcut(QKeySequence.StandardKey.Save); save_action.triggered.connect(self.save_project_action); file_menu.addAction(save_action)
        save_as_action = QAction("Save Project &As...", self); save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs); save_as_action.triggered.connect(self.save_project_as_action); file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self); exit_action.setShortcut(QKeySequence.StandardKey.Quit); exit_action.triggered.connect(self.close); file_menu.addAction(exit_action)

        manage_menu = menu_bar.addMenu("&Manage")
        
        # "Edit ItemLabels..." is kept as ItemLabels are simple strings
        edit_item_labels_action = QAction("Edit &ItemLabels...", self)
        edit_item_labels_action.triggered.connect(self.edit_item_labels)
        manage_menu.addAction(edit_item_labels_action)
        
        manage_menu.addSeparator() 
        
        # "Edit ActionLabels" and "Edit SubActionLabels" are removed.
        # These labels will be managed directly within their respective definition dialogs.

        edit_subaction_defs_action = QAction("Edit SubAction &Definitions...", self)
        edit_subaction_defs_action.triggered.connect(self.edit_sub_action_definitions)
        manage_menu.addAction(edit_subaction_defs_action)
        
        # manage_menu.addSeparator() # Separator can be removed if next item is related
        edit_action_defs_action = QAction("Edit Action De&finitions...", self)
        edit_action_defs_action.triggered.connect(self.edit_action_definitions) 
        manage_menu.addAction(edit_action_defs_action)
        
        manage_menu.addSeparator()
        edit_session_flows_action = QAction("Edit Session &Flows...", self) 
        edit_session_flows_action.triggered.connect(self.edit_session_graphs) 
        manage_menu.addAction(edit_session_flows_action)

        self.statusBar().showMessage("Ready")

    def _update_window_title(self):
        base_title = "SessionActions Framework Tool"
        project_name_part = "Untitled"
        if self.current_project_filepath:
            project_name_part = os.path.basename(self.current_project_filepath)
        elif self.current_project_data and self.current_project_data.project_metadata.project_name not in [None, "New SessionActions Project", ""]:
            project_name_part = self.current_project_data.project_metadata.project_name
        dirty_marker = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{base_title} - {project_name_part}{dirty_marker}")

    def _check_unsaved_changes(self) -> bool:
        if not self.is_dirty: return True
        reply = QMessageBox.question(self, "Unsaved Changes", "You have unsaved changes. Do you want to save them before proceeding?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Save: return self.save_project_action()
        elif reply == QMessageBox.StandardButton.Cancel: return False
        return True

    def mark_dirty(self, dirty_status: bool = True):
        if self.is_dirty != dirty_status:
            self.is_dirty = dirty_status
            self._update_window_title()

    @Slot()
    def new_project_action(self):
        if not self._check_unsaved_changes(): return
        self.new_project()
        self.statusBar().showMessage("New project created.", 5000)

    def new_project(self):
        self.current_project_data = json_handler.new_project(project_name="New SessionActions Project")
        self.current_project_filepath = None
        self.mark_dirty(False)
        self._update_window_title()
        if self.current_project_data: self.placeholder_label.setText(f"New Project: {self.current_project_data.project_metadata.project_name}\nUse 'Manage' menu to edit definitions and session flows.")
        else: self.placeholder_label.setText("Error: Could not initialize new project data.")
        print("New project initialized.")

    @Slot()
    def open_project_action(self):
        if not self._check_unsaved_changes(): return
        start_dir = os.getcwd() 
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Project File", start_dir, "JSON Files (*.json);;All Files (*)")
        if filepath:
            try:
                self.current_project_data = json_handler.load_project(filepath)
                self.current_project_filepath = filepath
                self.mark_dirty(False) 
                self._update_window_title()
                self.statusBar().showMessage(f"Project '{os.path.basename(filepath)}' loaded.", 5000)
                if self.current_project_data: self.placeholder_label.setText(f"Loaded Project: {self.current_project_data.project_metadata.project_name}\nUse 'Manage' menu to edit definitions and session flows.")
                else: self.placeholder_label.setText(f"Error: Could not load project data from {filepath}")
                print(f"Project loaded from: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading Project", f"Could not load project file:\n{filepath}\n\nError: {e}")
                self.statusBar().showMessage(f"Error loading project: {e}", 8000)

    @Slot()
    def save_project_action(self) -> bool:
        if not self.current_project_data:
            QMessageBox.warning(self, "No Project", "There is no project data to save.")
            return False
        if not self.current_project_filepath: return self.save_project_as_action()
        else:
            try:
                json_handler.save_project(self.current_project_data, self.current_project_filepath)
                self.mark_dirty(False) 
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
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Project As", start_dir, "JSON Files (*.json);;All Files (*)")
        if filepath:
            self.current_project_filepath = filepath 
            return self.save_project_action() 
        return False

    # edit_action_labels and edit_subaction_labels are removed.
    # The LabelEditorWidget is now only used for ItemLabels.
    @Slot()
    def edit_item_labels(self):
        if self.current_project_data: 
            self._open_label_editor_dialog(
                title="Edit ItemLabels", 
                getter=lambda: self.current_project_data.item_labels, 
                setter=lambda lst: setattr(self.current_project_data, 'item_labels', lst)
            )

    def _open_label_editor_dialog(self, title: str, getter: Callable[[], List[str]], setter: Callable[[List[str]], None]):
        # This function is now only for ItemLabels
        if not self.current_project_data:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return
        dialog = QDialog(self); dialog.setWindowTitle(title); dialog.setMinimumWidth(400); dialog.setMinimumHeight(300)
        layout = QVBoxLayout(dialog)
        # LabelEditorWidget is still used here for ItemLabels
        editor_widget = LabelEditorWidget(
            widget_title=title, # Pass title to widget if it uses it
            get_labels_func=getter, 
            set_labels_func=setter, 
            parent=dialog
        )
        editor_widget.labels_changed.connect(lambda: self.mark_dirty(True))
        layout.addWidget(editor_widget); dialog.setLayout(layout); dialog.exec()


    @Slot()
    def edit_sub_action_definitions(self):
        if not self.current_project_data:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return
        dialog = ManageSubActionDefinitionsDialog(self.current_project_data, self)
        dialog.project_data_changed.connect(lambda: self.mark_dirty(True))
        dialog.exec()

    @Slot()
    def edit_action_definitions(self):
        if not self.current_project_data:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return
        dialog = ManageActionDefinitionsDialog(self.current_project_data, self)
        dialog.project_data_changed.connect(lambda: self.mark_dirty(True))
        dialog.exec()

    @Slot()
    def edit_session_graphs(self): 
        if not self.current_project_data:
            QMessageBox.information(self, "No Project", "Please open or create a project first.")
            return
        if not self.current_project_data.action_definitions:
            QMessageBox.warning(self, "No Action Definitions", 
                                "Please define some Actions in 'Manage -> Edit Action Definitions' before creating Session Flows.")
            return
        dialog = ManageSessionActionsDialog(self.current_project_data, self)
        dialog.project_data_changed.connect(lambda: self.mark_dirty(True))
        dialog.exec()

    def closeEvent(self, event):
        if self._check_unsaved_changes(): event.accept(); print("Application closing.")
        else: event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("TestOrg")
    QApplication.setApplicationName("MainWindowTest - SessionActions") 
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
