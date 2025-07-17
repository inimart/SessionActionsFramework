# framework_tool/gui/dialogs/manage_sub_action_definitions_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QSplitter, QMessageBox, QInputDialog,
    QWidget, QLabel, QLineEdit # Added QLabel, QLineEdit for filter
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, Dict, List

from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.sub_action_definition import SubActionDefinition
from ..widgets.sub_action_definition_editor_widget import SubActionDefinitionEditorWidget


class ManageSubActionDefinitionsDialog(QDialog):
    """
    Dialog for managing all SubActionDefinitions in a project.
    Allows adding, removing SubActionLabels, and editing their definitions.
    Includes filtering for the SubActionLabel list.
    """
    project_data_changed = Signal() 

    def __init__(self, project_data: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data 

        self.setWindowTitle("Manage SubAction Definitions")
        self.setMinimumSize(800, 600)

        self._init_ui()
        self._load_sub_action_labels_list() # Initial population
        self._apply_filter() # Apply filter (empty at first)
        
        if self.sub_action_labels_list_widget.count() > 0:
            # Select the first visible item after filtering
            for i in range(self.sub_action_labels_list_widget.count()):
                if not self.sub_action_labels_list_widget.item(i).isHidden():
                    self.sub_action_labels_list_widget.setCurrentRow(i)
                    break
            if not self.sub_action_labels_list_widget.currentItem() and self.sub_action_labels_list_widget.count() > 0 :
                 self.sub_action_labels_list_widget.setCurrentRow(0) # Fallback if all are hidden initially (should not happen)
        else:
            self.editor_widget.load_sub_action_definition("", None)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Panel (List of SubActionLabels with Filter) ---
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        
        # Filter input
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:", self))
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Filter SubAction labels...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)
        left_layout.addLayout(filter_layout)
        
        self.sub_action_labels_list_widget = QListWidget(self)
        # self.sub_action_labels_list_widget.setSortingEnabled(True) # Sorting handled by _load_sub_action_labels_list
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

        splitter.setSizes([250, 550]) 
        main_layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.clicked.connect(self.accept) 
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def _load_sub_action_labels_list(self):
        """Populates the QListWidget with ALL SubActionLabels from project_data. Filtering is separate."""
        self.sub_action_labels_list_widget.blockSignals(True) 
        
        # Store current selection to try and restore it
        current_selected_text = None
        if self.sub_action_labels_list_widget.currentItem():
            current_selected_text = self.sub_action_labels_list_widget.currentItem().text()

        self.sub_action_labels_list_widget.clear()
        
        sorted_labels = sorted(self.project_data.sub_action_labels)
        for label in sorted_labels:
            self.sub_action_labels_list_widget.addItem(QListWidgetItem(label))
            
        self.sub_action_labels_list_widget.blockSignals(False)
        
        # Re-apply filter which will also handle visibility
        self._apply_filter() 

        # Try to restore selection if possible
        if current_selected_text:
            items = self.sub_action_labels_list_widget.findItems(current_selected_text, Qt.MatchFlag.MatchExactly)
            if items and not items[0].isHidden():
                self.sub_action_labels_list_widget.setCurrentItem(items[0])
            elif self.sub_action_labels_list_widget.count() > 0: # If old selection gone or hidden, select first visible
                for i in range(self.sub_action_labels_list_widget.count()):
                    if not self.sub_action_labels_list_widget.item(i).isHidden():
                        self.sub_action_labels_list_widget.setCurrentRow(i)
                        break
        elif self.sub_action_labels_list_widget.count() > 0: # Default to first visible if no prior selection
            for i in range(self.sub_action_labels_list_widget.count()):
                if not self.sub_action_labels_list_widget.item(i).isHidden():
                    self.sub_action_labels_list_widget.setCurrentRow(i)
                    break
        
        # If still no selection and list is not empty (e.g. all items hidden by filter)
        # then trigger a selection change with None to clear the editor.
        if not self.sub_action_labels_list_widget.currentItem() and self.sub_action_labels_list_widget.count() > 0 :
            self._on_selected_sub_action_label_changed(None, None)
        elif self.sub_action_labels_list_widget.count() == 0: # List is truly empty
             self._on_selected_sub_action_label_changed(None, None)


    @Slot(str)
    def _apply_filter(self):
        """Filters the items in the list widget based on the filter text."""
        filter_text = self.filter_input.text().lower()
        first_visible_item = None
        current_item_still_visible = False
        selected_item_text = self.sub_action_labels_list_widget.currentItem().text() if self.sub_action_labels_list_widget.currentItem() else None

        for i in range(self.sub_action_labels_list_widget.count()):
            item = self.sub_action_labels_list_widget.item(i)
            if item:
                item_is_visible = filter_text in item.text().lower()
                item.setHidden(not item_is_visible)
                if item_is_visible and not first_visible_item:
                    first_visible_item = item
                if item.text() == selected_item_text and item_is_visible:
                    current_item_still_visible = True
        
        # If current selection is now hidden, try to select the first visible item
        if selected_item_text and not current_item_still_visible:
            if first_visible_item:
                self.sub_action_labels_list_widget.setCurrentItem(first_visible_item)
            else: # No items are visible with current filter
                self._on_selected_sub_action_label_changed(None, self.sub_action_labels_list_widget.currentItem()) # Clear editor
        elif not selected_item_text and first_visible_item: # If no selection but there are visible items
             self.sub_action_labels_list_widget.setCurrentItem(first_visible_item)


    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selected_sub_action_label_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if current:
            label_key = current.text()
            definition = self.project_data.sub_action_definitions.get(label_key)
            if definition:
                self.editor_widget.load_sub_action_definition(label_key, definition)
            else:
                # This can happen if a label was added but its definition was not (the bug)
                # Or if data is inconsistent.
                QMessageBox.warning(self, "Data Inconsistency", f"No definition found for SubActionLabel '{label_key}'. Please check project data or re-add if necessary.")
                self.editor_widget.load_sub_action_definition(label_key, None) 
        else:
            self.editor_widget.load_sub_action_definition("", None)

    @Slot()
    def _add_new_sub_action_label(self):
        new_label, ok = QInputDialog.getText(self, "Add New SubActionLabel", "Enter name for the new SubActionLabel:")
        if ok and new_label:
            new_label = new_label.strip()
            if not new_label:
                QMessageBox.warning(self, "Input Error", "SubActionLabel name cannot be empty."); return

            if any(new_label.lower() == lbl.lower() for lbl in self.project_data.sub_action_labels):
                QMessageBox.warning(self, "Duplicate Label", f"The SubActionLabel '{new_label}' already exists."); return

            self.project_data.sub_action_labels.append(new_label)
            # CRITICAL FIX: Also create the definition object
            self.project_data.sub_action_definitions[new_label] = SubActionDefinition() 

            self._load_sub_action_labels_list() # Refresh & re-filter

            items = self.sub_action_labels_list_widget.findItems(new_label, Qt.MatchFlag.MatchExactly)
            if items and not items[0].isHidden(): # Select if visible
                self.sub_action_labels_list_widget.setCurrentItem(items[0])
            
            self.project_data_changed.emit() 
        elif ok and not new_label:
             QMessageBox.warning(self, "Input Error", "SubActionLabel name cannot be empty.")

    @Slot()
    def _remove_selected_sub_action_label(self):
        current_item = self.sub_action_labels_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a SubActionLabel to remove."); return

        label_to_remove = current_item.text()

        # --- Data Integrity Check ---
        is_used = False
        for action_def in self.project_data.action_definitions.values():
            for conf_sub_action in action_def.sub_actions:
                if conf_sub_action.sub_action_label_to_use == label_to_remove:
                    is_used = True
                    break
            if is_used:
                break
        
        if is_used:
            QMessageBox.warning(self, "Cannot Remove", 
                                f"SubActionLabel '{label_to_remove}' is currently in use by one or more Action Definitions. "
                                "Please remove its usages first.")
            return
        # --- End of Data Integrity Check ---

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
            
            self._load_sub_action_labels_list() 
            self.project_data_changed.emit()

    @Slot()
    def _on_definition_editor_changed(self):
        self.project_data_changed.emit()
