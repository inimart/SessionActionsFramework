# framework_tool/gui/dialogs/manage_action_definitions_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QSplitter, QMessageBox, QInputDialog,
    QWidget, QLabel, QLineEdit # Added QLabel, QLineEdit for filter
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, Dict, List

from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.action_definition import ActionDefinition 
from ..widgets.action_definition_editor_widget import ActionDefinitionEditorWidget


class ManageActionDefinitionsDialog(QDialog):
    """
    Dialog for managing all ActionDefinitions in a project.
    Allows adding, removing ActionLabels, and editing their definitions.
    Includes filtering for the ActionLabel list.
    """
    project_data_changed = Signal() 

    def __init__(self, project_data: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data 

        self.setWindowTitle("Manage Action Definitions")
        self.setMinimumSize(900, 700) 

        self._init_ui()
        self._load_action_labels_list() # Initial population
        self._apply_filter() # Apply filter (empty at first)
        
        if self.action_labels_list_widget.count() > 0:
            # Select the first visible item after filtering
            for i in range(self.action_labels_list_widget.count()):
                if not self.action_labels_list_widget.item(i).isHidden():
                    self.action_labels_list_widget.setCurrentRow(i)
                    break
            if not self.action_labels_list_widget.currentItem() and self.action_labels_list_widget.count() > 0 :
                 self.action_labels_list_widget.setCurrentRow(0) # Fallback
        else:
            self.editor_widget.load_action_definition("", None)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Panel (List of ActionLabels with Filter) ---
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)

        # Filter input
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:", self))
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Filter Action labels...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)
        left_layout.addLayout(filter_layout)
        
        self.action_labels_list_widget = QListWidget(self)
        # self.action_labels_list_widget.setSortingEnabled(True) # Sorting handled by _load_action_labels_list
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
        """Populates the QListWidget with ALL ActionLabels from project_data. Filtering is separate."""
        self.action_labels_list_widget.blockSignals(True)
        
        current_selected_text = None
        if self.action_labels_list_widget.currentItem():
            current_selected_text = self.action_labels_list_widget.currentItem().text()
            
        self.action_labels_list_widget.clear()
        
        sorted_labels = sorted(self.project_data.action_labels)
        for label in sorted_labels:
            self.action_labels_list_widget.addItem(QListWidgetItem(label))
            
        self.action_labels_list_widget.blockSignals(False)

        self._apply_filter() # Re-apply filter

        # Try to restore selection
        if current_selected_text:
            items = self.action_labels_list_widget.findItems(current_selected_text, Qt.MatchFlag.MatchExactly)
            if items and not items[0].isHidden():
                self.action_labels_list_widget.setCurrentItem(items[0])
            elif self.action_labels_list_widget.count() > 0: # Select first visible if old one gone/hidden
                for i in range(self.action_labels_list_widget.count()):
                    if not self.action_labels_list_widget.item(i).isHidden():
                        self.action_labels_list_widget.setCurrentRow(i)
                        break
        elif self.action_labels_list_widget.count() > 0: # Default to first visible
             for i in range(self.action_labels_list_widget.count()):
                if not self.action_labels_list_widget.item(i).isHidden():
                    self.action_labels_list_widget.setCurrentRow(i)
                    break
        
        if not self.action_labels_list_widget.currentItem() and self.action_labels_list_widget.count() > 0 :
            self._on_selected_action_label_changed(None, None)
        elif self.action_labels_list_widget.count() == 0:
             self._on_selected_action_label_changed(None, None)


    @Slot(str)
    def _apply_filter(self):
        """Filters the items in the list widget based on the filter text."""
        filter_text = self.filter_input.text().lower()
        first_visible_item = None
        current_item_still_visible = False
        selected_item_text = self.action_labels_list_widget.currentItem().text() if self.action_labels_list_widget.currentItem() else None

        for i in range(self.action_labels_list_widget.count()):
            item = self.action_labels_list_widget.item(i)
            if item:
                item_is_visible = filter_text in item.text().lower()
                item.setHidden(not item_is_visible)
                if item_is_visible and not first_visible_item:
                    first_visible_item = item
                if item.text() == selected_item_text and item_is_visible:
                    current_item_still_visible = True
        
        if selected_item_text and not current_item_still_visible:
            if first_visible_item:
                self.action_labels_list_widget.setCurrentItem(first_visible_item)
            else: 
                self._on_selected_action_label_changed(None, self.action_labels_list_widget.currentItem())
        elif not selected_item_text and first_visible_item:
             self.action_labels_list_widget.setCurrentItem(first_visible_item)


    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selected_action_label_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if current:
            label_key = current.text()
            definition = self.project_data.action_definitions.get(label_key)
            if definition:
                self.editor_widget.load_action_definition(label_key, definition)
            else:
                QMessageBox.warning(self, "Data Inconsistency", f"No definition found for ActionLabel '{label_key}'. Please check project data or re-add if necessary.")
                self.editor_widget.load_action_definition(label_key, None) 
        else:
            self.editor_widget.load_action_definition("", None)

    @Slot()
    def _add_new_action_label(self):
        new_label, ok = QInputDialog.getText(self, "Add New ActionLabel", "Enter name for the new ActionLabel:")
        if ok and new_label:
            new_label = new_label.strip()
            if not new_label:
                QMessageBox.warning(self, "Input Error", "ActionLabel name cannot be empty."); return

            if any(new_label.lower() == lbl.lower() for lbl in self.project_data.action_labels):
                QMessageBox.warning(self, "Duplicate Label", f"The ActionLabel '{new_label}' already exists."); return

            self.project_data.action_labels.append(new_label)
            # CRITICAL FIX: Also create the definition object
            self.project_data.action_definitions[new_label] = ActionDefinition() 

            self._load_action_labels_list() 

            items = self.action_labels_list_widget.findItems(new_label, Qt.MatchFlag.MatchExactly)
            if items and not items[0].isHidden(): # Select if visible
                self.action_labels_list_widget.setCurrentItem(items[0])
            
            self.project_data_changed.emit() 
        elif ok and not new_label:
             QMessageBox.warning(self, "Input Error", "ActionLabel name cannot be empty.")

    @Slot()
    def _remove_selected_action_label(self):
        current_item = self.action_labels_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select an ActionLabel to remove."); return

        label_to_remove = current_item.text()

        # --- Data Integrity Check ---
        is_used = False
        if self.project_data.session_actions:
            for session_graph in self.project_data.session_actions:
                for node in session_graph.nodes:
                    if node.action_label_to_execute == label_to_remove:
                        is_used = True
                        break
                if is_used:
                    break
        
        if is_used:
            QMessageBox.warning(self, "Cannot Remove", 
                                f"ActionLabel '{label_to_remove}' is currently in use by one or more Session Flow nodes. "
                                "Please remove its usages first.")
            return
        # --- End of Data Integrity Check ---
        
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
        self.project_data_changed.emit()
