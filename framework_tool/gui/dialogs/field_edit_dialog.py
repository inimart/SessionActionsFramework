# framework_tool/gui/dialogs/field_edit_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QDoubleSpinBox, QSpinBox, QPushButton, QDialogButtonBox,
    QWidget, QStackedWidget, QFormLayout, QSpacerItem, QSizePolicy,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, Slot
from typing import Optional, Any, List

from ...data_models.common_types import FieldType # Relative import from parent's sibling
from ...data_models.sub_action_definition import SubActionFieldDefinition


class FieldEditDialog(QDialog):
    """
    A dialog for creating or editing a SubActionFieldDefinition.
    """
    def __init__(self,
                 existing_field_definition: Optional[SubActionFieldDefinition] = None,
                 existing_field_names: Optional[List[str]] = None, # To check for name uniqueness
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.existing_field_definition = existing_field_definition
        self.original_field_name = existing_field_definition.field_name if existing_field_definition else None
        self.existing_field_names = existing_field_names if existing_field_names else []

        self.setWindowTitle("Edit Field Definition" if existing_field_definition else "Add New Field Definition")
        self.setMinimumWidth(450)

        self._init_ui()
        if existing_field_definition:
            self._load_data(existing_field_definition)
        else:
            # Sensible defaults for a new field
            self.field_type_combo.setCurrentIndex(self.field_type_combo.findData(FieldType.STRING))
            self._update_default_value_widget(FieldType.STRING)


    def _init_ui(self):
        """Initializes the User Interface for the dialog."""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) # Helps with smaller dialogs

        # Field Name
        self.field_name_input = QLineEdit(self)
        form_layout.addRow("Field Name:", self.field_name_input)

        # Field Type
        self.field_type_combo = QComboBox(self)
        for ft in FieldType: # Populate with FieldType enum members
            self.field_type_combo.addItem(ft.value.capitalize().replace("_", " "), userData=ft) # User-friendly name, store enum member
        self.field_type_combo.currentIndexChanged.connect(self._on_field_type_changed)
        form_layout.addRow("Field Type:", self.field_type_combo)

        # Default Value (using QStackedWidget for dynamic input)
        form_layout.addRow(QLabel("Default Value:", self)) # Label for the entire default value section
        self.default_value_stack = QStackedWidget(self)
        self._create_default_value_widgets() # Create all possible input widgets
        form_layout.addWidget(self.default_value_stack) # Add QStackedWidget to the form

        # Enum Values (only for EnumString)
        self.enum_values_label = QLabel("Enum Values (comma-separated):", self)
        self.enum_values_input = QLineEdit(self)
        self.enum_values_input.setPlaceholderText("e.g., Value1,Value2,Value3")
        form_layout.addRow(self.enum_values_label, self.enum_values_input)

        layout.addLayout(form_layout)

        # Dialog Buttons (OK, Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initial state for EnumString related widgets
        self._update_enum_values_visibility(self.field_type_combo.currentData())


    def _create_default_value_widgets(self):
        """Creates all possible input widgets for the default_value_stack."""
        # Order of adding widgets here must match FieldType enum order if using index directly
        # Or, better, store them in a dictionary keyed by FieldType
        self.default_value_widgets: Dict[FieldType, QWidget] = {}

        # Boolean
        bool_widget = QCheckBox("Is Default True?", self)
        self.default_value_stack.addWidget(bool_widget)
        self.default_value_widgets[FieldType.BOOLEAN] = bool_widget

        # String, AssetPathString, ItemLabelReference
        string_widget = QLineEdit(self)
        self.default_value_stack.addWidget(string_widget)
        self.default_value_widgets[FieldType.STRING] = string_widget
        self.default_value_widgets[FieldType.ASSET_PATH_STRING] = QLineEdit(self) # Separate instance
        self.default_value_stack.addWidget(self.default_value_widgets[FieldType.ASSET_PATH_STRING])
        self.default_value_widgets[FieldType.ITEM_LABEL_REFERENCE] = QLineEdit(self) # Separate instance
        self.default_value_stack.addWidget(self.default_value_widgets[FieldType.ITEM_LABEL_REFERENCE])
        
        # Float
        float_widget = QDoubleSpinBox(self)
        float_widget.setRange(-1e9, 1e9) # A very large range
        float_widget.setDecimals(3)
        self.default_value_stack.addWidget(float_widget)
        self.default_value_widgets[FieldType.FLOAT] = float_widget

        # Integer
        int_widget = QSpinBox(self)
        int_widget.setRange(-2147483648, 2147483647) # Standard 32-bit integer range
        self.default_value_stack.addWidget(int_widget)
        self.default_value_widgets[FieldType.INTEGER] = int_widget

        # Vector2 (X, Y as QDoubleSpinBox in a QHBoxLayout)
        vec2_widget = QWidget(self)
        vec2_layout = QHBoxLayout(vec2_widget)
        vec2_layout.setContentsMargins(0,0,0,0)
        self.vec2_x = QDoubleSpinBox(vec2_widget); self.vec2_x.setToolTip("X")
        self.vec2_y = QDoubleSpinBox(vec2_widget); self.vec2_y.setToolTip("Y")
        for spinbox in [self.vec2_x, self.vec2_y]: spinbox.setRange(-1e9, 1e9); spinbox.setDecimals(3)
        vec2_layout.addWidget(QLabel("X:", vec2_widget)); vec2_layout.addWidget(self.vec2_x)
        vec2_layout.addWidget(QLabel("Y:", vec2_widget)); vec2_layout.addWidget(self.vec2_y)
        vec2_layout.addStretch()
        self.default_value_stack.addWidget(vec2_widget)
        self.default_value_widgets[FieldType.VECTOR2] = vec2_widget

        # Vector3 (X, Y, Z)
        vec3_widget = QWidget(self)
        vec3_layout = QHBoxLayout(vec3_widget)
        vec3_layout.setContentsMargins(0,0,0,0)
        self.vec3_x = QDoubleSpinBox(vec3_widget); self.vec3_x.setToolTip("X")
        self.vec3_y = QDoubleSpinBox(vec3_widget); self.vec3_y.setToolTip("Y")
        self.vec3_z = QDoubleSpinBox(vec3_widget); self.vec3_z.setToolTip("Z")
        for spinbox in [self.vec3_x, self.vec3_y, self.vec3_z]: spinbox.setRange(-1e9, 1e9); spinbox.setDecimals(3)
        vec3_layout.addWidget(QLabel("X:", vec3_widget)); vec3_layout.addWidget(self.vec3_x)
        vec3_layout.addWidget(QLabel("Y:", vec3_widget)); vec3_layout.addWidget(self.vec3_y)
        vec3_layout.addWidget(QLabel("Z:", vec3_widget)); vec3_layout.addWidget(self.vec3_z)
        vec3_layout.addStretch()
        self.default_value_stack.addWidget(vec3_widget)
        self.default_value_widgets[FieldType.VECTOR3] = vec3_widget
        
        # Quaternion (X, Y, Z, W)
        quat_widget = QWidget(self)
        quat_layout = QHBoxLayout(quat_widget)
        quat_layout.setContentsMargins(0,0,0,0)
        self.quat_x = QDoubleSpinBox(quat_widget); self.quat_x.setToolTip("X")
        self.quat_y = QDoubleSpinBox(quat_widget); self.quat_y.setToolTip("Y")
        self.quat_z = QDoubleSpinBox(quat_widget); self.quat_z.setToolTip("Z")
        self.quat_w = QDoubleSpinBox(quat_widget); self.quat_w.setToolTip("W"); self.quat_w.setValue(1.0) # Default W
        for spinbox in [self.quat_x, self.quat_y, self.quat_z, self.quat_w]: spinbox.setRange(-1.0, 1.0); spinbox.setDecimals(5) # Quaternions usually normalized
        quat_layout.addWidget(QLabel("X:", quat_widget)); quat_layout.addWidget(self.quat_x)
        quat_layout.addWidget(QLabel("Y:", quat_widget)); quat_layout.addWidget(self.quat_y)
        quat_layout.addWidget(QLabel("Z:", quat_widget)); quat_layout.addWidget(self.quat_z)
        quat_layout.addWidget(QLabel("W:", quat_widget)); quat_layout.addWidget(self.quat_w)
        quat_layout.addStretch()
        self.default_value_stack.addWidget(quat_widget)
        self.default_value_widgets[FieldType.QUATERNION] = quat_widget

        # ColorRGBA (R, G, B, A - could add QColorDialog button later)
        color_widget = QWidget(self)
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0,0,0,0)
        self.color_r = QDoubleSpinBox(color_widget); self.color_r.setToolTip("Red")
        self.color_g = QDoubleSpinBox(color_widget); self.color_g.setToolTip("Green")
        self.color_b = QDoubleSpinBox(color_widget); self.color_b.setToolTip("Blue")
        self.color_a = QDoubleSpinBox(color_widget); self.color_a.setToolTip("Alpha"); self.color_a.setValue(1.0) # Default Alpha
        for spinbox in [self.color_r, self.color_g, self.color_b, self.color_a]: spinbox.setRange(0.0, 1.0); spinbox.setDecimals(3) # Color 0-1 range
        color_layout.addWidget(QLabel("R:", color_widget)); color_layout.addWidget(self.color_r)
        color_layout.addWidget(QLabel("G:", color_widget)); color_layout.addWidget(self.color_g)
        color_layout.addWidget(QLabel("B:", color_widget)); color_layout.addWidget(self.color_b)
        color_layout.addWidget(QLabel("A:", color_widget)); color_layout.addWidget(self.color_a)
        color_layout.addStretch()
        self.default_value_stack.addWidget(color_widget)
        self.default_value_widgets[FieldType.COLOR_RGBA] = color_widget
        
        # EnumString - Default value for EnumString is not directly set here,
        # or could be a ComboBox if enumValues were known at this stage.
        # For simplicity, EnumString won't have a default value input in this dialog,
        # or it's expected to be one of the enum_values string.
        # We add a placeholder widget for EnumString if needed.
        enum_default_placeholder = QLabel("N/A for EnumString (set from Enum Values)", self)
        self.default_value_stack.addWidget(enum_default_placeholder)
        self.default_value_widgets[FieldType.ENUM_STRING] = enum_default_placeholder
        
        # Placeholder for any types not explicitly handled (should not happen with current FieldType enum)
        self.default_value_stack.addWidget(QLabel("No default value input for this type.", self))


    def _update_default_value_widget(self, field_type: FieldType):
        """Switches the QStackedWidget to show the correct input for the FieldType."""
        if field_type in self.default_value_widgets:
            self.default_value_stack.setCurrentWidget(self.default_value_widgets[field_type])
        else:
            # Fallback to the last widget (placeholder "No default value input")
            self.default_value_stack.setCurrentIndex(self.default_value_stack.count() - 1)


    def _update_enum_values_visibility(self, field_type: FieldType):
        """Shows or hides the Enum Values input based on FieldType."""
        is_enum_string = (field_type == FieldType.ENUM_STRING)
        self.enum_values_label.setVisible(is_enum_string)
        self.enum_values_input.setVisible(is_enum_string)


    @Slot(int)
    def _on_field_type_changed(self, index: int):
        """Handles changes in the Field Type QComboBox."""
        selected_field_type = self.field_type_combo.itemData(index)
        if selected_field_type:
            self._update_default_value_widget(selected_field_type)
            self._update_enum_values_visibility(selected_field_type)

    def _load_data(self, field_def: SubActionFieldDefinition):
        """Populates dialog fields from an existing SubActionFieldDefinition."""
        self.field_name_input.setText(field_def.field_name)
        
        # Select correct FieldType in ComboBox
        type_index = self.field_type_combo.findData(field_def.field_type)
        if type_index >= 0:
            self.field_type_combo.setCurrentIndex(type_index)
        
        self._update_default_value_widget(field_def.field_type) # Ensure correct widget is shown
        self._update_enum_values_visibility(field_def.field_type)

        # Set default value based on type
        dv = field_def.default_value
        if dv is not None:
            current_widget = self.default_value_stack.currentWidget()
            if field_def.field_type == FieldType.BOOLEAN and isinstance(current_widget, QCheckBox):
                current_widget.setChecked(bool(dv))
            elif field_def.field_type in [FieldType.STRING, FieldType.ASSET_PATH_STRING, FieldType.ITEM_LABEL_REFERENCE] and isinstance(current_widget, QLineEdit):
                current_widget.setText(str(dv))
            elif field_def.field_type == FieldType.FLOAT and isinstance(current_widget, QDoubleSpinBox):
                current_widget.setValue(float(dv))
            elif field_def.field_type == FieldType.INTEGER and isinstance(current_widget, QSpinBox):
                current_widget.setValue(int(dv))
            elif field_def.field_type == FieldType.VECTOR2 and isinstance(dv, dict):
                self.vec2_x.setValue(float(dv.get("x", 0.0)))
                self.vec2_y.setValue(float(dv.get("y", 0.0)))
            elif field_def.field_type == FieldType.VECTOR3 and isinstance(dv, dict):
                self.vec3_x.setValue(float(dv.get("x", 0.0)))
                self.vec3_y.setValue(float(dv.get("y", 0.0)))
                self.vec3_z.setValue(float(dv.get("z", 0.0)))
            elif field_def.field_type == FieldType.QUATERNION and isinstance(dv, dict):
                self.quat_x.setValue(float(dv.get("x", 0.0)))
                self.quat_y.setValue(float(dv.get("y", 0.0)))
                self.quat_z.setValue(float(dv.get("z", 0.0)))
                self.quat_w.setValue(float(dv.get("w", 1.0)))
            elif field_def.field_type == FieldType.COLOR_RGBA and isinstance(dv, dict):
                self.color_r.setValue(float(dv.get("r", 0.0)))
                self.color_g.setValue(float(dv.get("g", 0.0)))
                self.color_b.setValue(float(dv.get("b", 0.0)))
                self.color_a.setValue(float(dv.get("a", 1.0)))
            # Default value for EnumString is not directly handled by a widget here,
            # but could be if we used a ComboBox populated by enum_values.

        if field_def.field_type == FieldType.ENUM_STRING and field_def.enum_values:
            self.enum_values_input.setText(",".join(field_def.enum_values))
        else:
            self.enum_values_input.clear()


    def get_field_definition(self) -> Optional[SubActionFieldDefinition]:
        """
        Retrieves the SubActionFieldDefinition from the dialog's current state.
        Performs validation. If validation fails, shows a message and returns None.
        """
        field_name = self.field_name_input.text().strip()
        if not field_name:
            QMessageBox.warning(self, "Input Error", "Field Name cannot be empty.")
            return None

        # Check for name uniqueness (excluding itself if editing)
        for existing_name in self.existing_field_names:
            if field_name.lower() == existing_name.lower() and \
               (self.original_field_name is None or field_name.lower() != self.original_field_name.lower()):
                QMessageBox.warning(self, "Input Error", f"Field Name '{field_name}' already exists (case-insensitive).")
                return None

        selected_field_type: FieldType = self.field_type_combo.currentData()
        default_value: Any = None
        enum_values_list: Optional[List[str]] = None

        # Get default value based on type
        current_default_widget = self.default_value_stack.currentWidget()
        try:
            if selected_field_type == FieldType.BOOLEAN and isinstance(current_default_widget, QCheckBox):
                default_value = current_default_widget.isChecked()
            elif selected_field_type in [FieldType.STRING, FieldType.ASSET_PATH_STRING, FieldType.ITEM_LABEL_REFERENCE] and isinstance(current_default_widget, QLineEdit):
                # Only set default if text is not empty, otherwise it's None (no default)
                default_value_text = current_default_widget.text().strip()
                if default_value_text: # Allow empty string as a valid default for string types if explicitly entered
                    default_value = default_value_text 
                else: # If user clears it, it means no default
                    default_value = None if selected_field_type == FieldType.STRING else None # Or "" for STRING? Let's go with None for no default.
                    if not current_default_widget.text(): # if truly empty, treat as no default
                        default_value = None

            elif selected_field_type == FieldType.FLOAT and isinstance(current_default_widget, QDoubleSpinBox):
                default_value = current_default_widget.value()
            elif selected_field_type == FieldType.INTEGER and isinstance(current_default_widget, QSpinBox):
                default_value = current_default_widget.value()
            elif selected_field_type == FieldType.VECTOR2:
                default_value = {"x": self.vec2_x.value(), "y": self.vec2_y.value()}
            elif selected_field_type == FieldType.VECTOR3:
                default_value = {"x": self.vec3_x.value(), "y": self.vec3_y.value(), "z": self.vec3_z.value()}
            elif selected_field_type == FieldType.QUATERNION:
                default_value = {"x": self.quat_x.value(), "y": self.quat_y.value(), "z": self.quat_z.value(), "w": self.quat_w.value()}
            elif selected_field_type == FieldType.COLOR_RGBA:
                default_value = {"r": self.color_r.value(), "g": self.color_g.value(), "b": self.color_b.value(), "a": self.color_a.value()}
            elif selected_field_type == FieldType.ENUM_STRING:
                # Default value for EnumString could be one of its enum_values.
                # For simplicity here, we might not set a default_value from UI,
                # or it could be a QComboBox if enum_values are already known.
                # Let's assume no settable default value from this dialog for EnumString now.
                default_value = None # Or handle based on a specific input widget for enum default
                
                enum_text = self.enum_values_input.text().strip()
                if not enum_text:
                    QMessageBox.warning(self, "Input Error", "Enum Values cannot be empty for EnumString type.")
                    return None
                enum_values_list = [val.strip() for val in enum_text.split(',') if val.strip()]
                if not enum_values_list:
                    QMessageBox.warning(self, "Input Error", "Enum Values must contain at least one value for EnumString type.")
                    return None
        except ValueError as ve: # Catch conversion errors from spinboxes etc.
            QMessageBox.warning(self, "Input Error", f"Invalid default value format: {ve}")
            return None

        # Special check: if all components of a vector/color/quat are at their "empty" defaults (e.g. 0 for vec/color, 0,0,0,1 for quat)
        # we might consider `default_value` as None to keep JSON clean, unless a non-zero default was intended.
        # For now, we'll store them as is. An "is default empty" checkbox could be added.

        try:
            return SubActionFieldDefinition(
                field_name=field_name,
                field_type=selected_field_type,
                default_value=default_value,
                enum_values=enum_values_list
            )
        except ValueError as ve: # Catch errors from SubActionFieldDefinition constructor (e.g. missing enum_values)
            QMessageBox.warning(self, "Definition Error", str(ve))
            return None

    # Override accept to perform validation before closing
    def accept(self):
        """Handles the OK button click, validates, and accepts the dialog."""
        # The actual SubActionFieldDefinition is retrieved by the caller using get_field_definition()
        # We just need to ensure it *can* be retrieved without error before accepting.
        if self.get_field_definition() is not None:
            super().accept()
        # else: validation message already shown by get_field_definition()

# --- Standalone Test ---
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)

    # Test 1: Add new field
    print("Test 1: Adding a new field")
    add_dialog = FieldEditDialog(existing_field_names=["existingField", "anotherField"])
    if add_dialog.exec() == QDialog.DialogCode.Accepted:
        new_field = add_dialog.get_field_definition()
        if new_field:
            print("New field created:")
            print(f"  Name: {new_field.field_name}")
            print(f"  Type: {new_field.field_type.value}")
            print(f"  Default: {new_field.default_value}")
            if new_field.enum_values:
                print(f"  Enum Values: {new_field.enum_values}")
            print("-" * 20)
    else:
        print("Add new field dialog cancelled.")
        print("-" * 20)

    # Test 2: Edit existing field
    print("\nTest 2: Editing an existing field")
    sample_field_to_edit = SubActionFieldDefinition(
        field_name="myVectorField",
        field_type=FieldType.VECTOR3,
        default_value={"x": 1.0, "y": 2.5, "z": -0.5}
    )
    edit_dialog = FieldEditDialog(
        existing_field_definition=sample_field_to_edit,
        existing_field_names=["existingField", "anotherField", "myVectorField"] # "myVectorField" is its own name
    )
    if edit_dialog.exec() == QDialog.DialogCode.Accepted:
        updated_field = edit_dialog.get_field_definition()
        if updated_field:
            print("Field updated:")
            print(f"  Name: {updated_field.field_name}")
            print(f"  Type: {updated_field.field_type.value}")
            print(f"  Default: {updated_field.default_value}")
            if updated_field.enum_values:
                print(f"  Enum Values: {updated_field.enum_values}")
            print("-" * 20)
    else:
        print("Edit field dialog cancelled.")
        print("-" * 20)

    # sys.exit(app.exec()) # Not needed for non-GUI test execution that just prints
    print("Dialog tests finished.")