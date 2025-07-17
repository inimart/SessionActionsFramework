# framework_tool/gui/widgets/action_definition_editor_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QComboBox, QDoubleSpinBox, QSpinBox, QStackedWidget, QFormLayout
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, List

# Import data models
from framework_tool.data_models.project_data import ProjectData 
from framework_tool.data_models.action_definition import ActionDefinition
from framework_tool.data_models.custom_field_definition import CustomFieldDefinition
from framework_tool.data_models.common_types import FieldType


class CustomFieldEditorDialog(QDialog):
    """Advanced dialog for editing custom field definitions with type-specific controls."""
    
    def __init__(self, existing_field: Optional[CustomFieldDefinition] = None, project_data_ref=None, parent=None):
        super().__init__(parent)
        self.existing_field = existing_field
        self.project_data_ref = project_data_ref
        self.setWindowTitle("Edit Custom Field" if existing_field else "Add Custom Field")
        self.setMinimumWidth(500)
        self._init_ui()
        
        if existing_field:
            self._load_field_data(existing_field)
        else:
            self._on_field_type_changed()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Field Name
        layout.addWidget(QLabel("Field Name:"))
        self.field_name_input = QLineEdit()
        layout.addWidget(self.field_name_input)
        
        # Field Type
        layout.addWidget(QLabel("Field Type:"))
        self.field_type_combo = QComboBox()
        for field_type in FieldType:
            self.field_type_combo.addItem(field_type.value.capitalize(), field_type)
        layout.addWidget(self.field_type_combo)
        
        # Default Value (type-specific controls)
        self.default_value_label = QLabel("Default Value:")
        layout.addWidget(self.default_value_label)
        
        # Stacked widget for different default value inputs
        self.default_value_stack = QStackedWidget()
        self._create_default_value_widgets()
        layout.addWidget(self.default_value_stack)
        
        # Enum Values (for EnumString only)
        self.enum_values_label = QLabel("Enum Values (comma-separated):")
        self.enum_values_input = QLineEdit()
        layout.addWidget(self.enum_values_label)
        layout.addWidget(self.enum_values_input)
        
        # Connect field type change to update UI
        self.field_type_combo.currentIndexChanged.connect(self._on_field_type_changed)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def _create_default_value_widgets(self):
        """Create type-specific input widgets."""
        self.widgets = {}
        
        # Boolean - Checkbox
        bool_widget = QCheckBox("Default value is True")
        self.default_value_stack.addWidget(bool_widget)
        self.widgets[FieldType.BOOLEAN] = bool_widget
        
        # String - Text field
        string_widget = QLineEdit()
        string_widget.setPlaceholderText("Enter default string value")
        self.default_value_stack.addWidget(string_widget)
        self.widgets[FieldType.STRING] = string_widget
        
        # Float - Spin box
        float_widget = QDoubleSpinBox()
        float_widget.setRange(-999999.99, 999999.99)
        float_widget.setDecimals(2)
        self.default_value_stack.addWidget(float_widget)
        self.widgets[FieldType.FLOAT] = float_widget
        
        # Integer - Spin box
        int_widget = QSpinBox()
        int_widget.setRange(-999999, 999999)
        self.default_value_stack.addWidget(int_widget)
        self.widgets[FieldType.INTEGER] = int_widget
        
        # Vector2 - Two input fields
        vec2_widget = QWidget()
        vec2_layout = QHBoxLayout(vec2_widget)
        vec2_layout.addWidget(QLabel("X:"))
        self.vec2_x = QDoubleSpinBox()
        self.vec2_x.setRange(-999999.99, 999999.99)
        self.vec2_x.setDecimals(2)
        vec2_layout.addWidget(self.vec2_x)
        vec2_layout.addWidget(QLabel("Y:"))
        self.vec2_y = QDoubleSpinBox()
        self.vec2_y.setRange(-999999.99, 999999.99)
        self.vec2_y.setDecimals(2)
        vec2_layout.addWidget(self.vec2_y)
        self.default_value_stack.addWidget(vec2_widget)
        self.widgets[FieldType.VECTOR2] = vec2_widget
        
        # Vector3 - Three input fields
        vec3_widget = QWidget()
        vec3_layout = QHBoxLayout(vec3_widget)
        vec3_layout.addWidget(QLabel("X:"))
        self.vec3_x = QDoubleSpinBox()
        self.vec3_x.setRange(-999999.99, 999999.99)
        self.vec3_x.setDecimals(2)
        vec3_layout.addWidget(self.vec3_x)
        vec3_layout.addWidget(QLabel("Y:"))
        self.vec3_y = QDoubleSpinBox()
        self.vec3_y.setRange(-999999.99, 999999.99)
        self.vec3_y.setDecimals(2)
        vec3_layout.addWidget(self.vec3_y)
        vec3_layout.addWidget(QLabel("Z:"))
        self.vec3_z = QDoubleSpinBox()
        self.vec3_z.setRange(-999999.99, 999999.99)
        self.vec3_z.setDecimals(2)
        vec3_layout.addWidget(self.vec3_z)
        self.default_value_stack.addWidget(vec3_widget)
        self.widgets[FieldType.VECTOR3] = vec3_widget
        
        # RGBA - Four input fields
        rgba_widget = QWidget()
        rgba_layout = QHBoxLayout(rgba_widget)
        rgba_layout.addWidget(QLabel("R:"))
        self.rgba_r = QDoubleSpinBox()
        self.rgba_r.setRange(0.0, 1.0)
        self.rgba_r.setDecimals(3)
        self.rgba_r.setValue(1.0)
        rgba_layout.addWidget(self.rgba_r)
        rgba_layout.addWidget(QLabel("G:"))
        self.rgba_g = QDoubleSpinBox()
        self.rgba_g.setRange(0.0, 1.0)
        self.rgba_g.setDecimals(3)
        self.rgba_g.setValue(1.0)
        rgba_layout.addWidget(self.rgba_g)
        rgba_layout.addWidget(QLabel("B:"))
        self.rgba_b = QDoubleSpinBox()
        self.rgba_b.setRange(0.0, 1.0)
        self.rgba_b.setDecimals(3)
        self.rgba_b.setValue(1.0)
        rgba_layout.addWidget(self.rgba_b)
        rgba_layout.addWidget(QLabel("A:"))
        self.rgba_a = QDoubleSpinBox()
        self.rgba_a.setRange(0.0, 1.0)
        self.rgba_a.setDecimals(3)
        self.rgba_a.setValue(1.0)
        rgba_layout.addWidget(self.rgba_a)
        self.default_value_stack.addWidget(rgba_widget)
        self.widgets[FieldType.RGBA] = rgba_widget
        
        # EnumString - Text field
        enum_widget = QLineEdit()
        enum_widget.setPlaceholderText("Default will be first enum value")
        enum_widget.setEnabled(False)
        self.default_value_stack.addWidget(enum_widget)
        self.widgets[FieldType.ENUM_STRING] = enum_widget
        
        # ItemLabelReference - Combo box
        item_combo = QComboBox()
        self.default_value_stack.addWidget(item_combo)
        self.widgets[FieldType.ITEM_LABEL_REFERENCE] = item_combo
    
    def _on_field_type_changed(self):
        """Update UI based on selected field type."""
        current_field_type = self.field_type_combo.currentData()
        
        # Switch to appropriate widget
        if current_field_type in self.widgets:
            widget = self.widgets[current_field_type]
            self.default_value_stack.setCurrentWidget(widget)
            
            # Populate ItemLabelReference combo if needed
            if current_field_type == FieldType.ITEM_LABEL_REFERENCE:
                self._populate_item_labels_combo()
        
        # Show/hide enum values based on field type
        is_enum = current_field_type == FieldType.ENUM_STRING
        self.enum_values_label.setVisible(is_enum)
        self.enum_values_input.setVisible(is_enum)
    
    def _populate_item_labels_combo(self):
        """Populate combo with available item labels."""
        combo = self.widgets[FieldType.ITEM_LABEL_REFERENCE]
        combo.clear()
        combo.addItem("[Not Set]", "")
        
        # Get item labels from project data
        if self.project_data_ref and hasattr(self.project_data_ref, 'item_labels'):
            item_labels = self.project_data_ref.item_labels
            for label in sorted(item_labels):
                combo.addItem(label, label)
    
    def _load_field_data(self, field: CustomFieldDefinition):
        self.field_name_input.setText(field.field_name)
        
        # Find and set field type
        for i in range(self.field_type_combo.count()):
            if self.field_type_combo.itemData(i) == field.field_type:
                self.field_type_combo.setCurrentIndex(i)
                break
        
        self._on_field_type_changed()  # Update UI first
        
        # Set default value based on field type
        if field.default_value is not None:
            if field.field_type == FieldType.BOOLEAN:
                self.widgets[FieldType.BOOLEAN].setChecked(bool(field.default_value))
            elif field.field_type == FieldType.STRING:
                self.widgets[FieldType.STRING].setText(str(field.default_value))
            elif field.field_type == FieldType.FLOAT:
                self.widgets[FieldType.FLOAT].setValue(float(field.default_value))
            elif field.field_type == FieldType.INTEGER:
                self.widgets[FieldType.INTEGER].setValue(int(field.default_value))
            elif field.field_type == FieldType.VECTOR2 and isinstance(field.default_value, dict):
                self.vec2_x.setValue(float(field.default_value.get("x", 0.0)))
                self.vec2_y.setValue(float(field.default_value.get("y", 0.0)))
            elif field.field_type == FieldType.VECTOR3 and isinstance(field.default_value, dict):
                self.vec3_x.setValue(float(field.default_value.get("x", 0.0)))
                self.vec3_y.setValue(float(field.default_value.get("y", 0.0)))
                self.vec3_z.setValue(float(field.default_value.get("z", 0.0)))
            elif field.field_type == FieldType.RGBA and isinstance(field.default_value, dict):
                self.rgba_r.setValue(float(field.default_value.get("r", 1.0)))
                self.rgba_g.setValue(float(field.default_value.get("g", 1.0)))
                self.rgba_b.setValue(float(field.default_value.get("b", 1.0)))
                self.rgba_a.setValue(float(field.default_value.get("a", 1.0)))
            elif field.field_type == FieldType.ITEM_LABEL_REFERENCE:
                combo = self.widgets[FieldType.ITEM_LABEL_REFERENCE]
                index = combo.findData(field.default_value)
                if index >= 0:
                    combo.setCurrentIndex(index)
        
        if field.enum_values:
            self.enum_values_input.setText(",".join(field.enum_values))
    
    def get_custom_field(self) -> Optional[CustomFieldDefinition]:
        field_name = self.field_name_input.text().strip()
        if not field_name:
            QMessageBox.warning(self, "Error", "Field name cannot be empty.")
            return None
        
        field_type = self.field_type_combo.currentData()
        default_value = None
        
        # Get default value based on field type
        if field_type == FieldType.BOOLEAN:
            default_value = self.widgets[FieldType.BOOLEAN].isChecked()
        elif field_type == FieldType.STRING:
            text = self.widgets[FieldType.STRING].text().strip()
            default_value = text if text else None
        elif field_type == FieldType.FLOAT:
            default_value = self.widgets[FieldType.FLOAT].value()
        elif field_type == FieldType.INTEGER:
            default_value = self.widgets[FieldType.INTEGER].value()
        elif field_type == FieldType.VECTOR2:
            default_value = {"x": self.vec2_x.value(), "y": self.vec2_y.value()}
        elif field_type == FieldType.VECTOR3:
            default_value = {"x": self.vec3_x.value(), "y": self.vec3_y.value(), "z": self.vec3_z.value()}
        elif field_type == FieldType.RGBA:
            default_value = {"r": self.rgba_r.value(), "g": self.rgba_g.value(), "b": self.rgba_b.value(), "a": self.rgba_a.value()}
        elif field_type == FieldType.ITEM_LABEL_REFERENCE:
            combo = self.widgets[FieldType.ITEM_LABEL_REFERENCE]
            default_value = combo.currentData()
            if default_value == "":  # "[Not Set]" option
                default_value = None
        elif field_type == FieldType.ENUM_STRING:
            # Default will be first enum value, set in enum_values logic below
            pass
        
        enum_values = None
        if field_type == FieldType.ENUM_STRING:
            enum_text = self.enum_values_input.text().strip()
            if enum_text:
                enum_values = [v.strip() for v in enum_text.split(",") if v.strip()]
                if enum_values:
                    default_value = enum_values[0]  # First enum value as default
        
        try:
            return CustomFieldDefinition(
                field_name=field_name,
                field_type=field_type,
                default_value=default_value,
                enum_values=enum_values
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create field: {e}")
            return None


class ActionDefinitionEditorWidget(QWidget):
    """
    A widget for editing a single ActionDefinition object, including its
    description, autocomplete flag, and custom fields.
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

        # Description
        description_layout = QHBoxLayout() 
        description_layout.addWidget(QLabel("Description:", self))
        self.description_input = QTextEdit(self)
        self.description_input.setFixedHeight(80)
        self.description_input.textChanged.connect(self._on_description_changed)
        description_layout.addWidget(self.description_input)
        main_layout.addLayout(description_layout)

        # Autocomplete checkbox
        self.autocomplete_checkbox = QCheckBox("Autocomplete (automatically complete this action)", self)
        self.autocomplete_checkbox.toggled.connect(self._on_autocomplete_changed)
        main_layout.addWidget(self.autocomplete_checkbox)

        # Custom Fields
        main_layout.addWidget(QLabel("Custom Fields:", self))
        self.custom_fields_table = QTableWidget(self)
        self.custom_fields_table.setColumnCount(3)
        self.custom_fields_table.setHorizontalHeaderLabels(["Field Name", "Type", "Default Value"])
        self.custom_fields_table.horizontalHeader().setStretchLastSection(True)
        self.custom_fields_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.custom_fields_table.doubleClicked.connect(self._edit_selected_custom_field)
        main_layout.addWidget(self.custom_fields_table)

        # Custom fields buttons
        fields_buttons_layout = QHBoxLayout()
        add_field_button = QPushButton("Add Field...", self)
        add_field_button.clicked.connect(self._add_custom_field)
        fields_buttons_layout.addWidget(add_field_button)

        edit_field_button = QPushButton("Edit Selected...", self)
        edit_field_button.clicked.connect(self._edit_selected_custom_field)
        fields_buttons_layout.addWidget(edit_field_button)

        remove_field_button = QPushButton("Remove Selected", self)
        remove_field_button.clicked.connect(self._remove_selected_custom_field)
        fields_buttons_layout.addWidget(remove_field_button)
        
        fields_buttons_layout.addStretch()
        main_layout.addLayout(fields_buttons_layout)
        
        self.setLayout(main_layout)
        self._enable_editing_controls(False) 

    def _enable_editing_controls(self, enabled: bool):
        self.description_input.setEnabled(enabled)
        self.autocomplete_checkbox.setEnabled(enabled)
        self.custom_fields_table.setEnabled(enabled)

    def load_action_definition(self, action_label: str, definition: Optional[ActionDefinition]):
        self._current_action_label_key = action_label
        self._current_action_definition = definition

        if definition:
            self.action_label_display.setText(f"Editing Action: {action_label}")
            
            self.description_input.blockSignals(True)
            self.autocomplete_checkbox.blockSignals(True)
            
            self.description_input.setText(definition.description or "")
            self.autocomplete_checkbox.setChecked(definition.autocomplete)
            
            self.description_input.blockSignals(False)
            self.autocomplete_checkbox.blockSignals(False)
            
            self._populate_custom_fields_table()
            self._enable_editing_controls(True)
        else:
            self.action_label_display.setText("Editing Action: [No Action Loaded]")
            self.description_input.clear()
            self.autocomplete_checkbox.setChecked(False)
            self.custom_fields_table.setRowCount(0)
            self._enable_editing_controls(False)

    def _populate_custom_fields_table(self):
        self.custom_fields_table.setRowCount(0)
        if not self._current_action_definition:
            return

        custom_fields = self._current_action_definition.custom_fields
        self.custom_fields_table.setRowCount(len(custom_fields))

        for row, field in enumerate(custom_fields):
            # Field name
            name_item = QTableWidgetItem(field.field_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.custom_fields_table.setItem(row, 0, name_item)
            
            # Field type
            type_item = QTableWidgetItem(field.field_type.value)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.custom_fields_table.setItem(row, 1, type_item)
            
            # Default value - format appropriately
            default_str = self._format_default_value(field)
            default_item = QTableWidgetItem(default_str)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.custom_fields_table.setItem(row, 2, default_item)
            
            # Store the field definition in the row
            self.custom_fields_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, field)

    def _format_default_value(self, field: CustomFieldDefinition) -> str:
        """Format default value for display in table."""
        if field.default_value is None:
            return "[Not Set]"
        
        if field.field_type == FieldType.BOOLEAN:
            return "True" if field.default_value else "False"
        elif field.field_type in [FieldType.STRING, FieldType.ENUM_STRING, FieldType.ITEM_LABEL_REFERENCE]:
            return str(field.default_value)
        elif field.field_type in [FieldType.FLOAT, FieldType.INTEGER]:
            return str(field.default_value)
        elif field.field_type == FieldType.VECTOR2:
            if isinstance(field.default_value, dict):
                return f"({field.default_value.get('x', 0)}, {field.default_value.get('y', 0)})"
        elif field.field_type == FieldType.VECTOR3:
            if isinstance(field.default_value, dict):
                return f"({field.default_value.get('x', 0)}, {field.default_value.get('y', 0)}, {field.default_value.get('z', 0)})"
        elif field.field_type == FieldType.RGBA:
            if isinstance(field.default_value, dict):
                return f"({field.default_value.get('r', 1)}, {field.default_value.get('g', 1)}, {field.default_value.get('b', 1)}, {field.default_value.get('a', 1)})"
        
        return str(field.default_value)

    @Slot()
    def _on_description_changed(self): 
        if self._current_action_definition:
            self._current_action_definition.description = self.description_input.toPlainText()
            self.action_definition_changed.emit()

    @Slot()
    def _on_autocomplete_changed(self, checked: bool):
        if self._current_action_definition:
            self._current_action_definition.autocomplete = checked
            self.action_definition_changed.emit()

    @Slot()
    def _add_custom_field(self):
        if not self._current_action_definition:
            return

        dialog = CustomFieldEditorDialog(project_data_ref=self.project_data_ref, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_field = dialog.get_custom_field()
            if new_field:
                # Check for duplicate field names
                existing_names = [f.field_name for f in self._current_action_definition.custom_fields]
                if new_field.field_name in existing_names:
                    QMessageBox.warning(self, "Duplicate Field", f"A field named '{new_field.field_name}' already exists.")
                    return
                
                self._current_action_definition.custom_fields.append(new_field)
                self._populate_custom_fields_table()
                self.action_definition_changed.emit()

    @Slot()
    def _edit_selected_custom_field(self):
        current_row = self.custom_fields_table.currentRow()
        if current_row < 0 or not self._current_action_definition:
            return

        field_to_edit = self.custom_fields_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        if not field_to_edit:
            return

        dialog = CustomFieldEditorDialog(existing_field=field_to_edit, project_data_ref=self.project_data_ref, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_field = dialog.get_custom_field()
            if updated_field:
                # Replace the field
                self._current_action_definition.custom_fields[current_row] = updated_field
                self._populate_custom_fields_table()
                self.action_definition_changed.emit()

    @Slot()
    def _remove_selected_custom_field(self):
        current_row = self.custom_fields_table.currentRow()
        if current_row < 0 or not self._current_action_definition:
            return

        field_name = self.custom_fields_table.item(current_row, 0).text()
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove the custom field '{field_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self._current_action_definition.custom_fields[current_row]
            self._populate_custom_fields_table()
            self.action_definition_changed.emit()