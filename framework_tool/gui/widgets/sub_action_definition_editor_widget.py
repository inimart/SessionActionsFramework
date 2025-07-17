# framework_tool/gui/widgets/sub_action_definition_editor_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog # <<<--- QDialog AGGIUNTO QUI
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, List

# Import data models
from framework_tool.data_models.sub_action_definition import SubActionDefinition, SubActionFieldDefinition
from framework_tool.data_models.common_types import FieldType

# Import the dialog for editing fields
from ..dialogs.field_edit_dialog import FieldEditDialog


class SubActionDefinitionEditorWidget(QWidget):
    """
    A widget for editing a single SubActionDefinition object,
    including its description, needsTargetItem flag, and its list of fields.
    """
    definition_changed = Signal() # Emitted when any part of the definition is modified

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._current_sub_action_definition: Optional[SubActionDefinition] = None
        self._current_sub_action_label_key: Optional[str] = None 

        self._init_ui()

    def _init_ui(self):
        """Initializes the User Interface for the widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0) 

        self.sub_action_label_display = QLabel("Editing: [No SubAction Loaded]")
        self.sub_action_label_display.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.sub_action_label_display)

        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Description:", self))
        self.description_input = QTextEdit(self) 
        self.description_input.setFixedHeight(60) 
        self.description_input.textChanged.connect(self._on_description_changed)
        description_layout.addWidget(self.description_input)
        main_layout.addLayout(description_layout)

        self.needs_target_item_checkbox = QCheckBox("Requires Target Item", self)
        self.needs_target_item_checkbox.stateChanged.connect(self._on_needs_target_item_changed)
        main_layout.addWidget(self.needs_target_item_checkbox)

        main_layout.addWidget(QLabel("Custom Fields:", self))
        self.fields_table = QTableWidget(self)
        self.fields_table.setColumnCount(4) 
        self.fields_table.setHorizontalHeaderLabels(["Field Name", "Field Type", "Default Value", "Enum Values"])
        self.fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fields_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fields_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.fields_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.fields_table.doubleClicked.connect(self._edit_selected_field_action) 
        main_layout.addWidget(self.fields_table)

        self.fields_buttons_widget = QWidget(self) 
        fields_buttons_layout = QHBoxLayout(self.fields_buttons_widget) 
        fields_buttons_layout.setContentsMargins(0,0,0,0)

        add_field_button = QPushButton("Add Field...", self)
        add_field_button.clicked.connect(self._add_field_action)
        fields_buttons_layout.addWidget(add_field_button)

        edit_field_button = QPushButton("Edit Selected Field...", self)
        edit_field_button.clicked.connect(self._edit_selected_field_action)
        fields_buttons_layout.addWidget(edit_field_button)

        remove_field_button = QPushButton("Remove Selected Field", self)
        remove_field_button.clicked.connect(self._remove_selected_field_action)
        fields_buttons_layout.addWidget(remove_field_button)
        fields_buttons_layout.addStretch()
        
        main_layout.addWidget(self.fields_buttons_widget) 
        
        self.setLayout(main_layout)
        self._enable_editing_controls(False) 

    def _enable_editing_controls(self, enabled: bool):
        """Enables or disables all editing controls."""
        self.description_input.setEnabled(enabled)
        self.needs_target_item_checkbox.setEnabled(enabled)
        self.fields_table.setEnabled(enabled)
        self.fields_buttons_widget.setEnabled(enabled)


    def load_sub_action_definition(self, sub_action_label: str, definition: Optional[SubActionDefinition]):
        self._current_sub_action_label_key = sub_action_label
        self._current_sub_action_definition = definition

        if definition:
            self.sub_action_label_display.setText(f"Editing: {sub_action_label}")
            
            self.description_input.blockSignals(True)
            self.needs_target_item_checkbox.blockSignals(True)
            
            self.description_input.setText(definition.description)
            self.needs_target_item_checkbox.setChecked(definition.needs_target_item)
            
            self.description_input.blockSignals(False)
            self.needs_target_item_checkbox.blockSignals(False)
            
            self._populate_fields_table()
            self._enable_editing_controls(True)
        else:
            self.sub_action_label_display.setText("Editing: [No SubAction Loaded]")
            self.description_input.clear()
            self.needs_target_item_checkbox.setChecked(False)
            self.fields_table.setRowCount(0)
            self._enable_editing_controls(False)

    def _populate_fields_table(self):
        self.fields_table.setRowCount(0) 
        if not self._current_sub_action_definition:
            return

        fields = sorted(self._current_sub_action_definition.fields, key=lambda f: f.field_name)
        self.fields_table.setRowCount(len(fields))

        for row, field_def in enumerate(fields):
            name_item = QTableWidgetItem(field_def.field_name)
            type_item = QTableWidgetItem(field_def.field_type.value.capitalize().replace("_", " "))
            
            default_val_str = "N/A"
            if field_def.default_value is not None:
                if isinstance(field_def.default_value, dict): 
                    default_val_str = ", ".join([f"{k}:{v:.2f}" if isinstance(v, float) else f"{k}:{v}" for k,v in field_def.default_value.items()])
                else:
                    default_val_str = str(field_def.default_value)
            default_item = QTableWidgetItem(default_val_str)
            
            enum_vals_str = "N/A"
            if field_def.field_type == FieldType.ENUM_STRING and field_def.enum_values:
                enum_vals_str = ", ".join(field_def.enum_values)
            enum_item = QTableWidgetItem(enum_vals_str)

            self.fields_table.setItem(row, 0, name_item)
            self.fields_table.setItem(row, 1, type_item)
            self.fields_table.setItem(row, 2, default_item)
            self.fields_table.setItem(row, 3, enum_item)
            
            self.fields_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, field_def)

    @Slot()
    def _on_description_changed(self):
        if self._current_sub_action_definition:
            self._current_sub_action_definition.description = self.description_input.toPlainText() 
            self.definition_changed.emit()

    @Slot(int)
    def _on_needs_target_item_changed(self, state: int):
        if self._current_sub_action_definition:
            self._current_sub_action_definition.needs_target_item = (state == Qt.CheckState.Checked.value)
            self.definition_changed.emit()

    @Slot()
    def _add_field_action(self):
        if not self._current_sub_action_definition:
            return

        existing_names = [f.field_name for f in self._current_sub_action_definition.fields]
        dialog = FieldEditDialog(existing_field_names=existing_names, parent=self)
        
        # QDialog.DialogCode.Accepted is the correct way to access this enum member
        if dialog.exec() == QDialog.DialogCode.Accepted: # No NameError if QDialog is imported
            new_field = dialog.get_field_definition()
            if new_field:
                self._current_sub_action_definition.fields.append(new_field)
                self._populate_fields_table()
                self.definition_changed.emit()

    @Slot()
    def _edit_selected_field_action(self):
        if not self._current_sub_action_definition:
            return

        selected_rows = self.fields_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a field to edit.")
            return
        
        selected_row_index = selected_rows[0].row()
        field_to_edit: Optional[SubActionFieldDefinition] = self.fields_table.item(selected_row_index, 0).data(Qt.ItemDataRole.UserRole)

        if not field_to_edit:
            QMessageBox.critical(self, "Error", "Could not retrieve field data for editing.")
            return

        existing_names = [f.field_name for f in self._current_sub_action_definition.fields]
        
        dialog = FieldEditDialog(
            existing_field_definition=field_to_edit,
            existing_field_names=existing_names,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted: # No NameError if QDialog is imported
            updated_field = dialog.get_field_definition()
            if updated_field:
                try:
                    original_index = -1
                    for i, field in enumerate(list(self._current_sub_action_definition.fields)): 
                        if field.field_name == field_to_edit.field_name: 
                            original_index = i
                            break
                    
                    if original_index != -1:
                         self._current_sub_action_definition.fields[original_index] = updated_field
                    else: 
                        try:
                            self._current_sub_action_definition.fields.remove(field_to_edit)
                        except ValueError:
                            pass 
                        self._current_sub_action_definition.fields.append(updated_field)

                    self._populate_fields_table()
                    self.definition_changed.emit()
                except Exception as e:
                     QMessageBox.critical(self, "Error", f"Failed to update field: {e}")

    @Slot()
    def _remove_selected_field_action(self):
        if not self._current_sub_action_definition:
            return

        selected_rows = self.fields_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a field to remove.")
            return

        selected_row_index = selected_rows[0].row()
        field_to_remove: Optional[SubActionFieldDefinition] = self.fields_table.item(selected_row_index, 0).data(Qt.ItemDataRole.UserRole)

        if not field_to_remove:
            QMessageBox.critical(self, "Error", "Could not retrieve field data for removal.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the field '{field_to_remove.field_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._current_sub_action_definition.fields.remove(field_to_remove)
                self._populate_fields_table()
                self.definition_changed.emit()
            except ValueError:
                found_and_removed = False
                for i, field in enumerate(self._current_sub_action_definition.fields):
                    if field.field_name == field_to_remove.field_name: 
                        del self._current_sub_action_definition.fields[i]
                        found_and_removed = True
                        break
                if found_and_removed:
                    self._populate_fields_table()
                    self.definition_changed.emit()
                else:
                    QMessageBox.critical(self, "Error", "Field not found in the current definition's list for removal.")

# --- Standalone Test (Optional - for testing this widget in isolation) ---
if __name__ == '__main__':
    # --- Bootstrap for standalone execution ---
    import sys
    import os
    if __package__ is None:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_script_dir)
        framework_tool_dir = os.path.dirname(gui_dir)
        project_root_dir = os.path.dirname(framework_tool_dir)
        if project_root_dir not in sys.path:
            sys.path.insert(0, project_root_dir)
    # --- End of Bootstrap ---
    
    from PySide6.QtWidgets import QApplication 

    from framework_tool.data_models.sub_action_definition import SubActionDefinition as TestSubActionDef, SubActionFieldDefinition as TestFieldDef
    from framework_tool.data_models.common_types import FieldType as TestFieldType

    app = QApplication(sys.argv)

    test_field1 = TestFieldDef("power", TestFieldType.INTEGER, default_value=100)
    test_field2 = TestFieldDef("targetTag", TestFieldType.STRING, default_value="Enemy")
    test_field3 = TestFieldDef(
        "effectType", TestFieldType.ENUM_STRING, 
        default_value="Fire", 
        enum_values=["Fire", "Ice", "Poison"]
    )
    dummy_sad = TestSubActionDef(
        description="A test SubAction with various fields.",
        needs_target_item=True,
        fields=[test_field1, test_field2, test_field3]
    )

    editor = SubActionDefinitionEditorWidget()
    editor.load_sub_action_definition("TestSubActionLabel", dummy_sad)
    
    @Slot()
    def on_def_changed():
        print("Standalone Test: SubActionDefinition changed!")
        if editor._current_sub_action_definition:
            print(f"  New Description: {editor._current_sub_action_definition.description}")
            print(f"  Needs Target: {editor._current_sub_action_definition.needs_target_item}")
            print(f"  Fields ({len(editor._current_sub_action_definition.fields)}):")
            for f_idx, f_def in enumerate(editor._current_sub_action_definition.fields):
                print(f"    {f_idx+1}. Name: {f_def.field_name}, Type: {f_def.field_type.value}, Default: {f_def.default_value}, Enums: {f_def.enum_values}")

    editor.definition_changed.connect(on_def_changed)
    
    editor.setWindowTitle("Test SubActionDefinition Editor")
    editor.resize(600, 500)
    editor.show()

    sys.exit(app.exec())
