# framework_tool/gui/widgets/action_definition_editor_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView,
    QDialog # <<<--- QDialog AGGIUNTO QUI
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, List

# Import data models
from ...data_models.project_data import ProjectData 
from ...data_models.action_definition import ActionDefinition, ConfiguredSubAction

# Import the dialog for adding/editing configured sub-actions
from ..dialogs.configured_sub_action_dialog import ConfiguredSubActionDialog


class ActionDefinitionEditorWidget(QWidget):
    """
    A widget for editing a single ActionDefinition object, including its
    helpLabel, description, and its ordered list of ConfiguredSubActions.
    """
    action_definition_changed = Signal() 

    def __init__(self, project_data_ref: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.project_data_ref = project_data_ref 
        
        self._current_action_definition: Optional[ActionDefinition] = None
        self._current_action_label_key: Optional[str] = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        self.action_label_display = QLabel("Editing Action: [No Action Loaded]")
        self.action_label_display.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.action_label_display)

        help_label_layout = QHBoxLayout()
        help_label_layout.addWidget(QLabel("Help Label (Tooltip):", self))
        self.help_label_input = QLineEdit(self)
        self.help_label_input.textChanged.connect(self._on_help_label_changed)
        help_label_layout.addWidget(self.help_label_input)
        main_layout.addLayout(help_label_layout)

        description_layout = QHBoxLayout() 
        description_layout.addWidget(QLabel("Description:", self))
        self.description_input = QTextEdit(self)
        self.description_input.setFixedHeight(80)
        self.description_input.textChanged.connect(self._on_description_changed)
        description_layout.addWidget(self.description_input)
        main_layout.addLayout(description_layout)

        main_layout.addWidget(QLabel("Configured SubActions (Sequence):", self))
        self.configured_sub_actions_list_widget = QListWidget(self)
        self.configured_sub_actions_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.configured_sub_actions_list_widget.doubleClicked.connect(self._edit_selected_configured_sub_action)
        main_layout.addWidget(self.configured_sub_actions_list_widget)

        self.csa_buttons_widget = QWidget(self) 
        csa_buttons_layout = QHBoxLayout(self.csa_buttons_widget)
        csa_buttons_layout.setContentsMargins(0,0,0,0)

        # Left column: Add, Edit, Remove in vertical
        left_buttons_layout = QVBoxLayout()
        add_csa_button = QPushButton("Add SubAction...", self)
        add_csa_button.clicked.connect(self._add_configured_sub_action)
        left_buttons_layout.addWidget(add_csa_button)

        edit_csa_button = QPushButton("Edit Selected...", self)
        edit_csa_button.clicked.connect(self._edit_selected_configured_sub_action)
        left_buttons_layout.addWidget(edit_csa_button)

        remove_csa_button = QPushButton("Remove Selected", self)
        remove_csa_button.clicked.connect(self._remove_selected_configured_sub_action)
        left_buttons_layout.addWidget(remove_csa_button)
        csa_buttons_layout.addLayout(left_buttons_layout)

        # Right column: Move Up, Move Down in vertical
        right_buttons_layout = QVBoxLayout()
        move_up_button = QPushButton("Move Up", self)
        move_up_button.clicked.connect(self._move_selected_csa_up)
        right_buttons_layout.addWidget(move_up_button)

        move_down_button = QPushButton("Move Down", self)
        move_down_button.clicked.connect(self._move_selected_csa_down)
        right_buttons_layout.addWidget(move_down_button)
        csa_buttons_layout.addLayout(right_buttons_layout)

        csa_buttons_layout.addStretch()
        main_layout.addWidget(self.csa_buttons_widget)
        
        self.setLayout(main_layout)
        self._enable_editing_controls(False) 

    def _enable_editing_controls(self, enabled: bool):
        self.help_label_input.setEnabled(enabled)
        self.description_input.setEnabled(enabled)
        self.configured_sub_actions_list_widget.setEnabled(enabled)
        self.csa_buttons_widget.setEnabled(enabled)

    def load_action_definition(self, action_label: str, definition: Optional[ActionDefinition]):
        self._current_action_label_key = action_label
        self._current_action_definition = definition

        if definition:
            self.action_label_display.setText(f"Editing Action: {action_label}")
            
            self.help_label_input.blockSignals(True)
            self.description_input.blockSignals(True)
            
            self.help_label_input.setText(definition.help_label or "")
            self.description_input.setText(definition.description or "")
            
            self.help_label_input.blockSignals(False)
            self.description_input.blockSignals(False)
            
            self._populate_configured_sub_actions_list()
            self._enable_editing_controls(True)
        else:
            self.action_label_display.setText("Editing Action: [No Action Loaded]")
            self.help_label_input.clear()
            self.description_input.clear()
            self.configured_sub_actions_list_widget.clear()
            self._enable_editing_controls(False)

    def _populate_configured_sub_actions_list(self):
        self.configured_sub_actions_list_widget.clear()
        if not self._current_action_definition:
            return

        for i, csa in enumerate(self._current_action_definition.sub_actions):
            item_text = f"{i+1}. {csa.sub_action_label_to_use}"
            if csa.item_label_for_target:
                item_text += f" (Target: {csa.item_label_for_target})"
            
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, csa) 
            self.configured_sub_actions_list_widget.addItem(list_item)

    @Slot()
    def _on_help_label_changed(self, text: str):
        if self._current_action_definition:
            self._current_action_definition.help_label = text
            self.action_definition_changed.emit()

    @Slot()
    def _on_description_changed(self): 
        if self._current_action_definition:
            self._current_action_definition.description = self.description_input.toPlainText()
            self.action_definition_changed.emit()

    @Slot()
    def _add_configured_sub_action(self):
        if not self._current_action_definition or not self.project_data_ref:
            QMessageBox.warning(self, "Error", "No current ActionDefinition or project data reference.")
            return

        dialog = ConfiguredSubActionDialog(project_data=self.project_data_ref, parent=self)
        # Use the QDialog.DialogCode enum for checking the result
        if dialog.exec() == QDialog.DialogCode.Accepted: # Corrected: QDialog was missing
            new_csa = dialog.get_configured_sub_action()
            if new_csa:
                self._current_action_definition.sub_actions.append(new_csa)
                self._populate_configured_sub_actions_list()
                self.action_definition_changed.emit()

    @Slot()
    def _edit_selected_configured_sub_action(self):
        if not self._current_action_definition or not self.project_data_ref:
            return
        
        selected_items = self.configured_sub_actions_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a SubAction to edit.")
            return
        
        current_list_item = selected_items[0]
        csa_to_edit: Optional[ConfiguredSubAction] = current_list_item.data(Qt.ItemDataRole.UserRole)
        original_index = self.configured_sub_actions_list_widget.row(current_list_item)

        if not csa_to_edit:
            QMessageBox.critical(self, "Error", "Could not retrieve SubAction data for editing.")
            return

        dialog = ConfiguredSubActionDialog(
            project_data=self.project_data_ref,
            existing_configured_sub_action=csa_to_edit,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted: # Corrected: QDialog was missing
            updated_csa = dialog.get_configured_sub_action()
            if updated_csa:
                if original_index >= 0 and original_index < len(self._current_action_definition.sub_actions):
                    self._current_action_definition.sub_actions[original_index] = updated_csa
                else: 
                    self._current_action_definition.sub_actions.append(updated_csa) 
                self._populate_configured_sub_actions_list()
                self.action_definition_changed.emit()

    @Slot()
    def _remove_selected_configured_sub_action(self):
        if not self._current_action_definition:
            return

        selected_items = self.configured_sub_actions_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a SubAction to remove.")
            return
            
        current_list_item = selected_items[0]
        row_to_remove = self.configured_sub_actions_list_widget.row(current_list_item)

        if row_to_remove >= 0:
            csa_summary = current_list_item.text() 
            reply = QMessageBox.question(
                self, "Confirm Removal",
                f"Are you sure you want to remove this SubAction?\n'{csa_summary}'",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self._current_action_definition.sub_actions[row_to_remove]
                self._populate_configured_sub_actions_list()
                self.action_definition_changed.emit()

    @Slot()
    def _move_selected_csa_up(self):
        if not self._current_action_definition or self.configured_sub_actions_list_widget.count() < 1:
            return

        current_row = self.configured_sub_actions_list_widget.currentRow()
        if current_row > 0: 
            csa_list = self._current_action_definition.sub_actions
            csa_list[current_row], csa_list[current_row - 1] = csa_list[current_row - 1], csa_list[current_row]
            self._populate_configured_sub_actions_list()
            self.configured_sub_actions_list_widget.setCurrentRow(current_row - 1) 
            self.action_definition_changed.emit()

    @Slot()
    def _move_selected_csa_down(self):
        if not self._current_action_definition or self.configured_sub_actions_list_widget.count() < 1:
            return

        current_row = self.configured_sub_actions_list_widget.currentRow()
        if current_row < self.configured_sub_actions_list_widget.count() - 1 and current_row != -1: 
            csa_list = self._current_action_definition.sub_actions
            csa_list[current_row], csa_list[current_row + 1] = csa_list[current_row + 1], csa_list[current_row]
            self._populate_configured_sub_actions_list()
            self.configured_sub_actions_list_widget.setCurrentRow(current_row + 1) 
            self.action_definition_changed.emit()

# (Standalone test code ommitted for brevity)
if __name__ == '__main__':
    import sys
    import os
    if __package__ is None: 
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_script_dir)
        framework_tool_dir = os.path.dirname(gui_dir)
        project_root_dir = os.path.dirname(framework_tool_dir)
        if project_root_dir not in sys.path:
            sys.path.insert(0, project_root_dir)
    from PySide6.QtWidgets import QApplication
    from framework_tool.data_models.project_data import ProjectData as TestProjectData
    from framework_tool.data_models.action_definition import ActionDefinition as TestActionDef, ConfiguredSubAction as TestConfiguredSA
    from framework_tool.data_models.sub_action_definition import SubActionDefinition as TestSubActionDef, SubActionFieldDefinition as TestFieldDef
    from framework_tool.data_models.common_types import FieldType as TestFieldType
    app = QApplication(sys.argv)
    dummy_project = TestProjectData()
    dummy_project.item_labels = ["Target_1", "Target_2"]
    sad1_fields = [TestFieldDef("paramA", TestFieldType.STRING)]
    sad1 = TestSubActionDef(description="SA1", fields=sad1_fields)
    dummy_project.sub_action_labels.append("SubActionTypeOne")
    dummy_project.sub_action_definitions["SubActionTypeOne"] = sad1
    sad2_fields = [TestFieldDef("valueB", TestFieldType.INTEGER, default_value=10)]
    sad2 = TestSubActionDef(description="SA2", needs_target_item=True, fields=sad2_fields)
    dummy_project.sub_action_labels.append("SubActionTypeTwo")
    dummy_project.sub_action_definitions["SubActionTypeTwo"] = sad2
    csa1 = TestConfiguredSA("SubActionTypeOne", property_values={"paramA": "Hello"})
    csa2 = TestConfiguredSA("SubActionTypeTwo", item_label_for_target="Target_1", property_values={"valueB": 25})
    dummy_ad = TestActionDef(help_label="Test Action Help", description="This is a test action definition.", sub_actions=[csa1, csa2])
    editor = ActionDefinitionEditorWidget(project_data_ref=dummy_project)
    editor.load_action_definition("TestActionLabel", dummy_ad)
    editor.action_definition_changed.connect(lambda: print("ActionDef changed (test)"))
    editor.setWindowTitle("Test ActionDefinition Editor")
    editor.resize(700, 500)
    editor.show()
    sys.exit(app.exec())
