# framework_tool/gui/main_window.py
# All comments and identifiers in English

import sys
import os
from typing import Optional, List, Callable 

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QMessageBox, QDialog, QSplitter, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QInputDialog, QTextEdit, QGroupBox
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, Slot, QSettings

from ..project_io import json_handler
from ..data_models.project_data import ProjectData
# from ..data_models.sub_action_definition import SubActionDefinition # Not directly used here
# from ..data_models.action_definition import ActionDefinition # Not directly used here
# from ..data_models.session_graph import SessionActionsGraph # Not directly used here

from .widgets.label_editor_widget import LabelEditorWidget
from .widgets.session_flow_editor_widget import SessionFlowEditorWidget
from .widgets.action_definition_editor_widget import ActionDefinitionEditorWidget
from .widgets.action_instance_customizer_widget import ActionInstanceCustomizerWidget


class MainWindow(QMainWindow):
    """
    The main window for the SessionActions Framework tool.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_project_data: Optional[ProjectData] = None
        self.current_project_filepath: Optional[str] = None
        self.is_dirty: bool = False
        self.settings = QSettings()
        # Load last used directory from settings
        self.last_used_directory = self.settings.value("last_used_directory", os.getcwd())
        self._init_ui()
        self.new_project()

    def _init_ui(self):
        self.setWindowTitle("SessionActions Framework Tool")
        self.setGeometry(100, 100, 1600, 900)

        central_widget = QWidget(self)
        self.main_layout = QVBoxLayout(central_widget)
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

        self._create_unified_interface()
        self._restore_layout()  # Restore layout after widgets are created
        self.statusBar().showMessage("Ready")

    def _create_unified_interface(self):
        """Create the unified 5-panel interface"""
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # 1. Session switcher (1 column)
        self._create_session_switcher_panel(self.main_splitter)
        
        # 2. Actions (2 columns) 
        self._create_actions_panel(self.main_splitter)
        
        # 3. Session Flow (1 column)
        self._create_session_flow_panel(self.main_splitter)
        
        # 4. Customize Action Instance (1 column)
        self._create_customize_action_instance_panel(self.main_splitter)
        
        # 5. Item labels (1 column)
        self._create_item_labels_panel(self.main_splitter)
        
        # Set initial splitter sizes: [Session, Actions, Flow, Customize, Items]
        self.main_splitter.setSizes([200, 500, 400, 300, 200])
        self.main_layout.addWidget(self.main_splitter)

    def _create_session_switcher_panel(self, parent_splitter):
        """Create Session switcher panel"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Session switcher", self))
        
        self.session_names_list_widget = QListWidget(self)
        self.session_names_list_widget.currentItemChanged.connect(self._on_selected_session_name_changed)
        layout.addWidget(self.session_names_list_widget)

        sessions_buttons_layout = QVBoxLayout()
        add_session_button = QPushButton("Add New Session...", self)
        add_session_button.clicked.connect(self._add_new_session)
        sessions_buttons_layout.addWidget(add_session_button)
        
        duplicate_session_button = QPushButton("Duplicate Session", self)
        duplicate_session_button.clicked.connect(self._duplicate_selected_session)
        sessions_buttons_layout.addWidget(duplicate_session_button)
        
        rename_session_button = QPushButton("Rename Session", self)
        rename_session_button.clicked.connect(self._rename_selected_session)
        sessions_buttons_layout.addWidget(rename_session_button)
        
        remove_session_button = QPushButton("Remove Selected", self)
        remove_session_button.clicked.connect(self._remove_selected_session)
        sessions_buttons_layout.addWidget(remove_session_button)
        layout.addLayout(sessions_buttons_layout)
        
        # Add Session Notes area
        notes_group = QGroupBox("Session Notes", self)
        notes_layout = QVBoxLayout(notes_group)
        
        self.session_notes_text_edit = QTextEdit(self)
        self.session_notes_text_edit.setPlaceholderText("Enter notes for the selected session...")
        self.session_notes_text_edit.textChanged.connect(self._on_session_notes_changed)
        notes_layout.addWidget(self.session_notes_text_edit)
        
        layout.addWidget(notes_group)
        
        parent_splitter.addWidget(panel)

    def _create_actions_panel(self, parent_splitter):
        """Create Actions panel (2 columns)"""
        self.actions_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # Left: Actions list
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Actions", self))
        
        # Filter input
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:", self))
        self.actions_filter_input = QLineEdit(self)
        self.actions_filter_input.setPlaceholderText("Filter Action labels...")
        self.actions_filter_input.textChanged.connect(self._apply_actions_filter)
        filter_layout.addWidget(self.actions_filter_input)
        left_layout.addLayout(filter_layout)
        
        self.action_labels_list_widget = QListWidget(self)
        self.action_labels_list_widget.currentItemChanged.connect(self._on_selected_action_label_changed)
        left_layout.addWidget(self.action_labels_list_widget)

        actions_buttons_layout = QVBoxLayout()
        add_action_button = QPushButton("Add New ActionLabel...", self)
        add_action_button.clicked.connect(self._add_new_action_label)
        actions_buttons_layout.addWidget(add_action_button)
        remove_action_button = QPushButton("Remove Selected ActionLabel", self)
        remove_action_button.clicked.connect(self._remove_selected_action_label)
        actions_buttons_layout.addWidget(remove_action_button)
        left_layout.addLayout(actions_buttons_layout)
        
        self.actions_splitter.addWidget(left_panel)

        # Right: Actions editor 
        self.action_editor_widget = ActionDefinitionEditorWidget(project_data_ref=None, parent=self)
        self.action_editor_widget.action_definition_changed.connect(self._on_action_definition_changed)
        self.actions_splitter.addWidget(self.action_editor_widget)
        
        self.actions_splitter.setSizes([300, 600])
        parent_splitter.addWidget(self.actions_splitter)

    def _create_session_flow_panel(self, parent_splitter):
        """Create Session Flow panel"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Session Flow", self))
        
        self.session_flow_editor_widget = SessionFlowEditorWidget(project_data_ref=None, parent=self)
        self.session_flow_editor_widget.session_graph_changed.connect(self._on_session_flow_changed)
        self.session_flow_editor_widget.action_node_selected.connect(self._on_action_node_selected_in_flow)
        layout.addWidget(self.session_flow_editor_widget)
        
        parent_splitter.addWidget(panel)

    def _create_customize_action_instance_panel(self, parent_splitter):
        """Create Customize Action Instance panel"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Customize Action Instance", self))
        
        # Use the ActionInstanceCustomizerWidget for editing action instance properties
        self.action_instance_customizer_widget = ActionInstanceCustomizerWidget(project_data_ref=self.current_project_data, parent=self)
        self.action_instance_customizer_widget.instance_changed.connect(self._on_action_instance_changed)
        layout.addWidget(self.action_instance_customizer_widget)
        
        parent_splitter.addWidget(panel)

    def _create_item_labels_panel(self, parent_splitter):
        """Create Item labels panel"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Item labels", self))
        
        self.item_labels_editor_widget = LabelEditorWidget(
            widget_title="Item labels",
            get_labels_func=lambda: self.current_project_data.item_labels if self.current_project_data else [],
            set_labels_func=lambda lst: setattr(self.current_project_data, 'item_labels', lst) if self.current_project_data else None,
            parent=self
        )
        self.item_labels_editor_widget.labels_changed.connect(lambda: self.mark_dirty(True))
        layout.addWidget(self.item_labels_editor_widget)
        
        parent_splitter.addWidget(panel)

    def _save_layout(self):
        """Save current layout to QSettings"""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Save splitter states
        self.settings.setValue("main_splitter", self.main_splitter.saveState())
        self.settings.setValue("actions_splitter", self.actions_splitter.saveState())

    def _restore_layout(self):
        """Restore layout from QSettings"""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restore splitter states (after widgets are created)
        main_splitter_state = self.settings.value("main_splitter")
        if main_splitter_state and hasattr(self, 'main_splitter'):
            self.main_splitter.restoreState(main_splitter_state)
        
        actions_splitter_state = self.settings.value("actions_splitter") 
        if actions_splitter_state and hasattr(self, 'actions_splitter'):
            self.actions_splitter.restoreState(actions_splitter_state)

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
    
    def _save_last_used_directory(self, filepath: str):
        """Save the directory of the given filepath as the last used directory."""
        if filepath:
            directory = os.path.dirname(filepath)
            if directory:
                self.last_used_directory = directory
                self.settings.setValue("last_used_directory", directory)

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
        self._refresh_all_panels()
        print("New project initialized.")

    @Slot()
    def open_project_action(self):
        if not self._check_unsaved_changes(): return
        # Use last used directory or current directory as fallback
        start_dir = self.last_used_directory if os.path.exists(self.last_used_directory) else os.getcwd()
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Project File", start_dir, "JSON Files (*.json);;All Files (*)")
        if filepath:
            try:
                self.current_project_data = json_handler.load_project(filepath)
                self.current_project_filepath = filepath
                self._save_last_used_directory(filepath)  # Save the directory for future use
                self.mark_dirty(False) 
                self._update_window_title()
                self.statusBar().showMessage(f"Project '{os.path.basename(filepath)}' loaded.", 5000)
                self._refresh_all_panels()
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
                self._save_last_used_directory(self.current_project_filepath)  # Save the directory for future use
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
        # Use the directory of current file if available, otherwise use last used directory
        if self.current_project_filepath:
            start_dir = os.path.dirname(self.current_project_filepath)
        else:
            start_dir = self.last_used_directory if os.path.exists(self.last_used_directory) else os.getcwd()
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Project As", start_dir, "JSON Files (*.json);;All Files (*)")
        if filepath:
            self.current_project_filepath = filepath
            self._save_last_used_directory(filepath)  # Save the directory for future use
            return self.save_project_action() 
        return False

    def _refresh_all_panels(self):
        """Refresh all panels when project data changes"""
        self._refresh_session_switcher()
        self._refresh_actions_panel()
        self._refresh_session_flow()
        self._refresh_customize_action_instance_panel()
        self._refresh_item_labels()

    def _refresh_session_switcher(self):
        """Refresh session switcher list"""
        if not self.current_project_data:
            self.session_names_list_widget.clear()
            return
            
        self.session_names_list_widget.blockSignals(True)
        self.session_names_list_widget.clear()
        sorted_sessions = sorted(self.current_project_data.session_actions, key=lambda s: s.session_name)
        for session_graph in sorted_sessions:
            self.session_names_list_widget.addItem(QListWidgetItem(session_graph.session_name))
        self.session_names_list_widget.blockSignals(False)

        if self.session_names_list_widget.count() > 0:
            self.session_names_list_widget.setCurrentRow(0)
        else:
            self.session_flow_editor_widget.load_session_graph("", None)
            self.session_notes_text_edit.clear()

    def _refresh_actions_panel(self):
        """Refresh actions list and filter"""
        # Update project data reference
        if hasattr(self, 'action_editor_widget'):
            self.action_editor_widget.project_data_ref = self.current_project_data
            
        if not self.current_project_data:
            self.action_labels_list_widget.clear()
            self.action_editor_widget.load_action_definition("", None)
            return
            
        self._load_action_labels_list()
        self._apply_actions_filter()

    def _refresh_session_flow(self):
        """Refresh session flow editor"""
        if hasattr(self, 'session_flow_editor_widget'):
            # Update project data reference
            self.session_flow_editor_widget.project_data_ref = self.current_project_data
    
    def _refresh_customize_action_instance_panel(self):
        """Refresh customize action instance panel"""
        if hasattr(self, 'action_instance_customizer_widget'):
            # Update project data reference
            self.action_instance_customizer_widget.project_data_ref = self.current_project_data
            # Clear details when project changes
            self.action_instance_customizer_widget.clear_details()


    def _refresh_item_labels(self):
        """Refresh item labels editor"""
        if hasattr(self, 'item_labels_editor_widget'):
            self.item_labels_editor_widget.load_labels()

    # Session switcher handlers
    def _on_selected_session_name_changed(self, current, previous):
        """Handle session selection change"""
        if not current or not self.current_project_data:
            self.session_flow_editor_widget.load_session_graph("", None)
            self.session_notes_text_edit.clear()
            return
        
        session_name = current.text()
        session_graph = next((s for s in self.current_project_data.session_actions if s.session_name == session_name), None)
        self.session_flow_editor_widget.load_session_graph(session_name, session_graph)
        
        # Update session notes
        if session_graph:
            self.session_notes_text_edit.blockSignals(True)
            self.session_notes_text_edit.setPlainText(session_graph.notes)
            self.session_notes_text_edit.blockSignals(False)

    def _add_new_session(self):
        """Add new session"""
        from framework_tool.data_models.session_graph import SessionActionsGraph
        
        if not self.current_project_data:
            return
            
        session_name, ok = QInputDialog.getText(self, "Add New Session", "Enter session name:")
        if ok and session_name.strip():
            session_name = session_name.strip()
            if any(s.session_name == session_name for s in self.current_project_data.session_actions):
                QMessageBox.warning(self, "Duplicate Name", f"A session with the name '{session_name}' already exists.")
                return
            
            new_session = SessionActionsGraph(session_name=session_name)
            self.current_project_data.session_actions.append(new_session)
            self._refresh_session_switcher()
            self.mark_dirty(True)

    def _remove_selected_session(self):
        """Remove selected session"""
        current = self.session_names_list_widget.currentItem()
        if not current or not self.current_project_data:
            return
            
        session_name = current.text()
        reply = QMessageBox.question(self, "Remove Session", 
                                   f"Are you sure you want to remove the session '{session_name}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.current_project_data.session_actions = [s for s in self.current_project_data.session_actions if s.session_name != session_name]
            self._refresh_session_switcher()
            self.mark_dirty(True)

    def _duplicate_selected_session(self):
        """Duplicate the selected session"""
        import copy
        from framework_tool.data_models.session_graph import SessionActionsGraph
        
        current = self.session_names_list_widget.currentItem()
        if not current or not self.current_project_data:
            return
            
        session_name = current.text()
        session_to_duplicate = next((s for s in self.current_project_data.session_actions if s.session_name == session_name), None)
        if not session_to_duplicate:
            return
            
        # Generate unique copy name
        copy_name = f"{session_name}_copy"
        copy_number = 1
        while any(s.session_name == copy_name for s in self.current_project_data.session_actions):
            copy_name = f"{session_name}_copy{copy_number}"
            copy_number += 1
            
        # Deep copy the session
        duplicated_session = SessionActionsGraph(
            session_name=copy_name,
            steps=copy.deepcopy(session_to_duplicate.steps),
            nodes=copy.deepcopy(session_to_duplicate.nodes),
            notes=session_to_duplicate.notes
        )
        
        self.current_project_data.session_actions.append(duplicated_session)
        self._refresh_session_switcher()
        
        # Select the new duplicated session
        for i in range(self.session_names_list_widget.count()):
            if self.session_names_list_widget.item(i).text() == copy_name:
                self.session_names_list_widget.setCurrentRow(i)
                break
                
        self.mark_dirty(True)

    def _rename_selected_session(self):
        """Rename the selected session"""
        current = self.session_names_list_widget.currentItem()
        if not current or not self.current_project_data:
            return
            
        old_name = current.text()
        new_name, ok = QInputDialog.getText(self, "Rename Session", "Enter new session name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # Check for duplicate name
            if any(s.session_name == new_name for s in self.current_project_data.session_actions):
                QMessageBox.warning(self, "Duplicate Name", f"A session with the name '{new_name}' already exists.")
                return
                
            # Find and rename the session
            session = next((s for s in self.current_project_data.session_actions if s.session_name == old_name), None)
            if session:
                session.session_name = new_name
                self._refresh_session_switcher()
                
                # Select the renamed session
                for i in range(self.session_names_list_widget.count()):
                    if self.session_names_list_widget.item(i).text() == new_name:
                        self.session_names_list_widget.setCurrentRow(i)
                        break
                        
                self.mark_dirty(True)

    def _on_session_notes_changed(self):
        """Handle session notes text change"""
        current = self.session_names_list_widget.currentItem()
        if not current or not self.current_project_data:
            return
            
        session_name = current.text()
        session = next((s for s in self.current_project_data.session_actions if s.session_name == session_name), None)
        if session:
            session.notes = self.session_notes_text_edit.toPlainText()
            self.mark_dirty(True)

    # Actions panel handlers
    def _load_action_labels_list(self):
        """Load action labels into list widget"""
        if not self.current_project_data:
            return
            
        self.action_labels_list_widget.blockSignals(True)
        current_selected_text = None
        if self.action_labels_list_widget.currentItem():
            current_selected_text = self.action_labels_list_widget.currentItem().text()
        
        self.action_labels_list_widget.clear()
        for action_label in sorted(set(self.current_project_data.action_labels)):
            self.action_labels_list_widget.addItem(QListWidgetItem(action_label))
        
        self.action_labels_list_widget.blockSignals(False)
        
        # Restore selection
        if current_selected_text:
            for i in range(self.action_labels_list_widget.count()):
                if self.action_labels_list_widget.item(i).text() == current_selected_text:
                    self.action_labels_list_widget.setCurrentRow(i)
                    break

    def _apply_actions_filter(self):
        """Apply filter to actions list"""
        filter_text = self.actions_filter_input.text().lower()
        for i in range(self.action_labels_list_widget.count()):
            item = self.action_labels_list_widget.item(i)
            item.setHidden(filter_text not in item.text().lower())

    def _on_selected_action_label_changed(self, current, previous):
        """Handle action selection change"""
        if not current or not self.current_project_data:
            self.action_editor_widget.load_action_definition("", None)
            return
        
        action_label = current.text()
        action_def = self.current_project_data.action_definitions.get(action_label)
        self.action_editor_widget.load_action_definition(action_label, action_def)

    def _add_new_action_label(self):
        """Add new action label"""
        if not self.current_project_data:
            return
            
        action_label, ok = QInputDialog.getText(self, "Add New Action Label", "Enter action label:")
        if ok and action_label.strip():
            action_label = action_label.strip()
            if action_label in self.current_project_data.action_labels:
                QMessageBox.warning(self, "Duplicate Label", f"Action label '{action_label}' already exists.")
                return
            
            from framework_tool.data_models.action_definition import ActionDefinition
            self.current_project_data.action_labels.append(action_label)
            self.current_project_data.action_definitions[action_label] = ActionDefinition()
            self._refresh_actions_panel()
            self.mark_dirty(True)

    def _remove_selected_action_label(self):
        """Remove selected action label"""
        current = self.action_labels_list_widget.currentItem()
        if not current or not self.current_project_data:
            return
            
        action_label = current.text()
        reply = QMessageBox.question(self, "Remove Action Label", 
                                   f"Are you sure you want to remove the action label '{action_label}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.current_project_data.action_labels = [al for al in self.current_project_data.action_labels if al != action_label]
            if action_label in self.current_project_data.action_definitions:
                del self.current_project_data.action_definitions[action_label]
            self._refresh_actions_panel()
            self.mark_dirty(True)

    def _on_action_definition_changed(self):
        """Handle action definition changes"""
        self.mark_dirty(True)
    
    def _on_action_instance_changed(self):
        """Handle action instance changes"""
        self.mark_dirty(True)
        # Refresh the flow to show updated instance labels and custom fields
        if hasattr(self, 'session_flow_editor_widget'):
            self.session_flow_editor_widget.refresh_current_view()

    # Session flow handlers
    def _on_session_flow_changed(self):
        """Handle session flow changes"""
        self.mark_dirty(True)

    def _on_action_node_selected_in_flow(self, action_node):
        """Handle action node selection in flow - sync with actions panel and update customize panel"""
        if not action_node or not self.current_project_data:
            if hasattr(self, 'action_instance_customizer_widget'):
                self.action_instance_customizer_widget.clear_details()
            return
            
        action_label = action_node.action_label_to_execute
        # Find and select the corresponding action in the actions list
        for i in range(self.action_labels_list_widget.count()):
            item = self.action_labels_list_widget.item(i)
            if item.text() == action_label and not item.isHidden():
                self.action_labels_list_widget.setCurrentRow(i)
                break
        
        # Update the customize action instance panel
        if hasattr(self, 'action_instance_customizer_widget'):
            self.action_instance_customizer_widget.load_action_node_details(action_node)


    def closeEvent(self, event):
        if self._check_unsaved_changes(): 
            self._save_layout()  # Save layout before closing
            event.accept(); 
            print("Application closing.")
        else: 
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("TestOrg")
    QApplication.setApplicationName("MainWindowTest - SessionActions") 
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
