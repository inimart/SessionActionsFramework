# framework_tool/gui/dialogs/manage_action_definitions_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QSplitter, QMessageBox, QInputDialog,
    QWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, Dict, List

from ...data_models.project_data import ProjectData
from ...data_models.action_definition import ActionDefinition # Import ActionDefinition
from ..widgets.action_definition_editor_widget import ActionDefinitionEditorWidget # Import the new editor


class ManageActionDefinitionsDialog(QDialog):
    """
    Dialog for managing all ActionDefinitions in a project.
    Allows adding, removing ActionLabels, and editing their definitions.
    """
    project_data_changed = Signal() 

    def __init__(self, project_data: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data 

        self.setWindowTitle("Manage Action Definitions")
        self.setMinimumSize(900, 700) # Larger dialog for more complex editor

        self._init_ui()
        self._load_action_labels_list()
        
        if self.action_labels_list_widget.count() > 0:
            self.action_labels_list_widget.setCurrentRow(0)
        else:
            self.editor_widget.load_action_definition("", None)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Panel (List of ActionLabels) ---
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        
        self.action_labels_list_widget = QListWidget(self)
        self.action_labels_list_widget.currentItemChanged.connect(self._on_selected_action_label_changed)
        left_layout.addWidget(self.action_labels_list_widget)

        labels_buttons_layout = QHBoxLayout()
        add_label_button = QPushButton("Add New ActionLabel...", self)
        add_label_button.clicked.connect(self._add_new_action_label)
        labels_buttons_layout.addWidget(add_label_button)

        remove_label_button = QPushButton("Remove Selected ActionLabel", self)
        remove_label_button.clicked.connect(self._remove_selected_action_label)
        labels_buttons_layout.addWidget(remove_label_button)
        left_layout.addLayout(labels_buttons_layout)
        
        splitter.addWidget(left_panel)

        # --- Right Panel (ActionDefinitionEditorWidget) ---
        # Pass the project_data_ref to the ActionDefinitionEditorWidget
        self.editor_widget = ActionDefinitionEditorWidget(project_data_ref=self.project_data, parent=self)
        self.editor_widget.action_definition_changed.connect(self._on_definition_editor_changed)
        splitter.addWidget(self.editor_widget)

        splitter.setSizes([300, 600]) 
        main_layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.clicked.connect(self.accept) 
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def _load_action_labels_list(self):
        """Populates the QListWidget with ActionLabels from project_data."""
        self.action_labels_list_widget.blockSignals(True)
        self.action_labels_list_widget.clear()
        
        sorted_labels = sorted(self.project_data.action_labels)
        for label in sorted_labels:
            self.action_labels_list_widget.addItem(QListWidgetItem(label))
            
        self.action_labels_list_widget.blockSignals(False)

        if self.action_labels_list_widget.count() > 0:
            if not self.action_labels_list_widget.currentItem():
                 self.action_labels_list_widget.setCurrentRow(0)
            else:
                 self._on_selected_action_label_changed(self.action_labels_list_widget.currentItem(), None)
        else: 
            self.editor_widget.load_action_definition("", None)


    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selected_action_label_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Loads the definition for the newly selected ActionLabel."""
        if current:
            label_key = current.text()
            definition = self.project_data.action_definitions.get(label_key)
            if definition:
                self.editor_widget.load_action_definition(label_key, definition)
            else:
                QMessageBox.critical(self, "Data Error", f"No definition found for ActionLabel '{label_key}'.")
                self.editor_widget.load_action_definition(label_key, None)
        else:
            self.editor_widget.load_action_definition("", None)

    @Slot()
    def _add_new_action_label(self):
        """Prompts for a new ActionLabel, adds it, and creates an empty definition."""
        new_label, ok = QInputDialog.getText(self, "Add New ActionLabel", "Enter name for the new ActionLabel:")
        if ok and new_label:
            new_label = new_label.strip()
            if not new_label:
                QMessageBox.warning(self, "Input Error", "ActionLabel name cannot be empty.")
                return

            if any(new_label.lower() == lbl.lower() for lbl in self.project_data.action_labels):
                QMessageBox.warning(self, "Duplicate Label", f"The ActionLabel '{new_label}' already exists.")
                return

            self.project_data.action_labels.append(new_label)
            self.project_data.action_definitions[new_label] = ActionDefinition() # Create empty definition

            self._load_action_labels_list() 

            items = self.action_labels_list_widget.findItems(new_label, Qt.MatchFlag.MatchExactly)
            if items:
                self.action_labels_list_widget.setCurrentItem(items[0])
            
            self.project_data_changed.emit() 
        elif ok and not new_label:
             QMessageBox.warning(self, "Input Error", "ActionLabel name cannot be empty.")


    @Slot()
    def _remove_selected_action_label(self):
        """Removes the selected ActionLabel and its definition."""
        current_item = self.action_labels_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select an ActionLabel to remove.")
            return

        label_to_remove = current_item.text()

        # TODO: Add check: is this ActionLabel used by any SessionActionsGraph?
        # For now, simple removal.
        
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove ActionLabel '{label_to_remove}' and its definition?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if label_to_remove in self.project_data.action_labels:
                self.project_data.action_labels.remove(label_to_remove)
            if label_to_remove in self.project_data.action_definitions:
                del self.project_data.action_definitions[label_to_remove]
            
            self._load_action_labels_list() 
            self.project_data_changed.emit()

    @Slot()
    def _on_definition_editor_changed(self):
        """Called when the ActionDefinitionEditorWidget signals a change."""
        self.project_data_changed.emit()

