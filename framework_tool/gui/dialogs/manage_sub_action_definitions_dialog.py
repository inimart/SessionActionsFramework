# framework_tool/gui/dialogs/manage_sub_action_definitions_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QSplitter, QMessageBox, QInputDialog,
    QWidget # Added QWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, Dict, List

from ...data_models.project_data import ProjectData
from ...data_models.sub_action_definition import SubActionDefinition
from ..widgets.sub_action_definition_editor_widget import SubActionDefinitionEditorWidget


class ManageSubActionDefinitionsDialog(QDialog):
    """
    Dialog for managing all SubActionDefinitions in a project.
    Allows adding, removing SubActionLabels, and editing their definitions.
    """
    # Emitted when any change is made that should mark the main project as dirty
    project_data_changed = Signal() 

    def __init__(self, project_data: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data # Direct reference to the main project data

        self.setWindowTitle("Manage SubAction Definitions")
        self.setMinimumSize(800, 600)

        self._init_ui()
        self._load_sub_action_labels_list()
        
        # Select first item if list is not empty
        if self.sub_action_labels_list_widget.count() > 0:
            self.sub_action_labels_list_widget.setCurrentRow(0)
        else:
            # If no labels, disable the editor part initially
            self.editor_widget.load_sub_action_definition("", None)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Panel (List of SubActionLabels) ---
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        
        self.sub_action_labels_list_widget = QListWidget(self)
        self.sub_action_labels_list_widget.currentItemChanged.connect(self._on_selected_sub_action_label_changed)
        left_layout.addWidget(self.sub_action_labels_list_widget)

        labels_buttons_layout = QHBoxLayout()
        add_label_button = QPushButton("Add New SubActionLabel...", self)
        add_label_button.clicked.connect(self._add_new_sub_action_label)
        labels_buttons_layout.addWidget(add_label_button)

        remove_label_button = QPushButton("Remove Selected SubActionLabel", self)
        remove_label_button.clicked.connect(self._remove_selected_sub_action_label)
        labels_buttons_layout.addWidget(remove_label_button)
        left_layout.addLayout(labels_buttons_layout)
        
        splitter.addWidget(left_panel)

        # --- Right Panel (SubActionDefinitionEditorWidget) ---
        self.editor_widget = SubActionDefinitionEditorWidget(self)
        self.editor_widget.definition_changed.connect(self._on_definition_editor_changed)
        splitter.addWidget(self.editor_widget)

        splitter.setSizes([250, 550]) # Initial sizes for left and right panels
        main_layout.addWidget(splitter)

        # --- Dialog Buttons (Close) ---
        # Changes are applied directly to project_data, so "OK/Apply" is implicit.
        # "Close" is enough. Unsaved changes are handled by the main window.
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.clicked.connect(self.accept) # Use accept to close dialog
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def _load_sub_action_labels_list(self):
        """Populates the QListWidget with SubActionLabels from project_data."""
        self.sub_action_labels_list_widget.blockSignals(True) # Avoid triggering selection change while populating
        self.sub_action_labels_list_widget.clear()
        
        # Sort labels alphabetically for display
        sorted_labels = sorted(self.project_data.sub_action_labels)
        for label in sorted_labels:
            self.sub_action_labels_list_widget.addItem(QListWidgetItem(label))
            
        self.sub_action_labels_list_widget.blockSignals(False)

        # After loading, if there are items, select the first one to trigger loading its definition
        # Or restore previous selection if that's desired (more complex)
        if self.sub_action_labels_list_widget.count() > 0:
            # If no item is current, set the first one.
            # This will also trigger _on_selected_sub_action_label_changed if an item becomes current.
            if not self.sub_action_labels_list_widget.currentItem():
                 self.sub_action_labels_list_widget.setCurrentRow(0)
            else: # If an item was already current (e.g. after add/remove), re-trigger selection
                 self._on_selected_sub_action_label_changed(self.sub_action_labels_list_widget.currentItem(), None)

        else: # No labels exist
            self.editor_widget.load_sub_action_definition("", None)


    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selected_sub_action_label_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Loads the definition for the newly selected SubActionLabel."""
        if current:
            label_key = current.text()
            definition = self.project_data.sub_action_definitions.get(label_key)
            if definition:
                self.editor_widget.load_sub_action_definition(label_key, definition)
            else:
                # This case should ideally not happen if data is consistent
                QMessageBox.critical(self, "Data Error", f"No definition found for SubActionLabel '{label_key}'.")
                self.editor_widget.load_sub_action_definition(label_key, None) # Clear editor
        else:
            # No item selected, clear the editor
            self.editor_widget.load_sub_action_definition("", None)

    @Slot()
    def _add_new_sub_action_label(self):
        """Prompts for a new SubActionLabel, adds it, and creates an empty definition."""
        new_label, ok = QInputDialog.getText(self, "Add New SubActionLabel", "Enter name for the new SubActionLabel:")
        if ok and new_label:
            new_label = new_label.strip()
            if not new_label:
                QMessageBox.warning(self, "Input Error", "SubActionLabel name cannot be empty.")
                return

            # Check for duplicates (case-insensitive)
            if any(new_label.lower() == lbl.lower() for lbl in self.project_data.sub_action_labels):
                QMessageBox.warning(self, "Duplicate Label", f"The SubActionLabel '{new_label}' already exists.")
                return

            # Add to project_data
            self.project_data.sub_action_labels.append(new_label)
            self.project_data.sub_action_definitions[new_label] = SubActionDefinition() # Create empty definition

            self._load_sub_action_labels_list() # Refresh the list

            # Find and select the newly added item
            items = self.sub_action_labels_list_widget.findItems(new_label, Qt.MatchFlag.MatchExactly)
            if items:
                self.sub_action_labels_list_widget.setCurrentItem(items[0])
            
            self.project_data_changed.emit() # Signal that project data has changed
        elif ok and not new_label:
             QMessageBox.warning(self, "Input Error", "SubActionLabel name cannot be empty.")


    @Slot()
    def _remove_selected_sub_action_label(self):
        """Removes the selected SubActionLabel and its definition."""
        current_item = self.sub_action_labels_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a SubActionLabel to remove.")
            return

        label_to_remove = current_item.text()

        # TODO: Add check here: is this SubActionLabel used by any ActionDefinition?
        # If so, warn the user or prevent deletion. For now, simple removal.
        # Example check (would require access to all ActionDefinitions):
        # is_used = any(
        #    configured_sa.sub_action_label_to_use == label_to_remove
        #    for action_def in self.project_data.action_definitions.values()
        #    for configured_sa in action_def.sub_actions
        # )
        # if is_used:
        #     QMessageBox.warning(self, "Cannot Remove", f"SubActionLabel '{label_to_remove}' is currently in use by one or more Action Definitions.")
        #     return

        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove SubActionLabel '{label_to_remove}' and its definition?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if label_to_remove in self.project_data.sub_action_labels:
                self.project_data.sub_action_labels.remove(label_to_remove)
            if label_to_remove in self.project_data.sub_action_definitions:
                del self.project_data.sub_action_definitions[label_to_remove]
            
            self._load_sub_action_labels_list() # Refresh list (will also clear editor if list becomes empty or selection changes)
            self.project_data_changed.emit()

    @Slot()
    def _on_definition_editor_changed(self):
        """Called when the SubActionDefinitionEditorWidget signals a change."""
        # The editor widget modifies the SubActionDefinition object directly.
        # We just need to signal that the overall project data is now dirty.
        self.project_data_changed.emit()

