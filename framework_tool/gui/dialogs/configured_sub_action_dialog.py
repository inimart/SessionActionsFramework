# framework_tool/gui/dialogs/configured_sub_action_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QCheckBox, QDoubleSpinBox, QSpinBox, QPushButton, QDialogButtonBox,
    QWidget, QStackedWidget, QFormLayout, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from typing import Optional, Any, List, Dict

from ...data_models.project_data import ProjectData
from ...data_models.action_definition import ConfiguredSubAction
from ...data_models.sub_action_definition import SubActionDefinition, SubActionFieldDefinition
from ...data_models.common_types import FieldType


class ConfiguredSubActionDialog(QDialog):
    """
    Dialog for creating or editing a ConfiguredSubAction instance.
    This involves selecting a SubActionLabel, an optional ItemLabel,
    and setting property values for the fields defined in the chosen SubActionDefinition.
    """
    def __init__(self,
                 project_data: ProjectData, 
                 existing_configured_sub_action: Optional[ConfiguredSubAction] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.project_data = project_data
        self.existing_configured_sub_action = existing_configured_sub_action
        
        self._current_selected_sub_action_def: Optional[SubActionDefinition] = None
        self._property_value_widgets: Dict[str, QWidget] = {}


        self.setWindowTitle("Edit Configured SubAction" if existing_configured_sub_action else "Add New Configured SubAction")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._init_ui() # This populates sub_action_label_combo

        if existing_configured_sub_action:
            self._load_data(existing_configured_sub_action)
        else:
            # Trigger update for property widgets based on initially selected SubActionLabel (if any)
            if self.sub_action_label_combo.count() > 0 and self.sub_action_label_combo.itemData(0) is not None:
                self._on_sub_action_label_selected(0) # Select first valid item by default
            else: 
                self._clear_property_widgets_area(add_placeholder_if_no_type=True) 
                self.item_label_combo.setEnabled(False)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.sub_action_label_combo = QComboBox(self)
        sorted_sub_action_labels = sorted(self.project_data.sub_action_labels)
        if not sorted_sub_action_labels:
            self.sub_action_label_combo.addItem("[No SubAction Types Defined]", userData=None)
            self.sub_action_label_combo.setEnabled(False)
        else:
            for label in sorted_sub_action_labels:
                definition = self.project_data.sub_action_definitions.get(label)
                if definition: 
                    self.sub_action_label_combo.addItem(label, userData=definition)
        self.sub_action_label_combo.currentIndexChanged.connect(self._on_sub_action_label_selected)
        form_layout.addRow("SubAction Type:", self.sub_action_label_combo)

        self.item_label_combo = QComboBox(self)
        self.item_label_combo.addItem("[No Target Item]", userData=None) 
        sorted_item_labels = sorted(self.project_data.item_labels)
        for label in sorted_item_labels:
            self.item_label_combo.addItem(label, userData=label)
        self.item_label_combo.setEnabled(False) 
        form_layout.addRow("Target ItemLabel:", self.item_label_combo)

        form_layout.addRow(QLabel("Property Values:", self))
        
        self.props_scroll_area = QScrollArea(self)
        self.props_scroll_area.setWidgetResizable(True)
        self.props_scroll_area.setMinimumHeight(150) 
        
        self.props_widget_container = QWidget() 
        self.props_form_layout = QFormLayout(self.props_widget_container)
        self.props_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.props_scroll_area.setWidget(self.props_widget_container)
        
        form_layout.addWidget(self.props_scroll_area)

        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    @Slot(int)
    def _on_sub_action_label_selected(self, index: int):
        selected_definition = self.sub_action_label_combo.itemData(index)
        if isinstance(selected_definition, SubActionDefinition):
            self._current_selected_sub_action_def = selected_definition
            self.item_label_combo.setEnabled(selected_definition.needs_target_item)
            if not selected_definition.needs_target_item:
                no_target_index = self.item_label_combo.findData(None)
                if no_target_index != -1:
                    self.item_label_combo.setCurrentIndex(no_target_index)
            self._populate_property_widgets(selected_definition.fields)
        else: 
            self._current_selected_sub_action_def = None
            self.item_label_combo.setEnabled(False)
            self._clear_property_widgets_area(add_placeholder_if_no_type=True)

    def _clear_property_widgets_area(self, add_placeholder_if_no_type: bool = False):
        # Clear existing widgets from the layout more robustly for QFormLayout
        while self.props_form_layout.rowCount() > 0:
            self.props_form_layout.removeRow(0)
        self._property_value_widgets.clear()
        
        if add_placeholder_if_no_type:
            # This placeholder is for when NO SubAction type is selected or valid
            placeholder_label = QLabel("[Select a SubAction Type to see its properties]", self.props_widget_container)
            self.props_form_layout.addRow(placeholder_label)


    def _populate_property_widgets(self, fields: List[SubActionFieldDefinition]):
        self._clear_property_widgets_area(add_placeholder_if_no_type=False) # Clear first

        if not fields:
            # This placeholder is for when a SubAction type IS selected, but it has NO fields
            placeholder_label = QLabel("[This SubAction type has no configurable properties]", self.props_widget_container)
            self.props_form_layout.addRow(placeholder_label)
            return

        for field_def in sorted(fields, key=lambda f: f.field_name):
            label_text = f"{field_def.field_name} ({field_def.field_type.value.capitalize().replace('_', ' ')}):"
            input_widget: Optional[QWidget] = None

            # --- Widget Creation (same as before, ensure this part is correct) ---
            if field_def.field_type == FieldType.BOOLEAN:
                input_widget = QCheckBox(self.props_widget_container)
                if field_def.default_value is not None: input_widget.setChecked(bool(field_def.default_value))
            
            elif field_def.field_type in [FieldType.STRING, FieldType.ASSET_PATH_STRING, FieldType.ITEM_LABEL_REFERENCE]:
                input_widget = QLineEdit(self.props_widget_container)
                if field_def.default_value is not None: input_widget.setText(str(field_def.default_value))
            
            elif field_def.field_type == FieldType.FLOAT:
                input_widget = QDoubleSpinBox(self.props_widget_container)
                input_widget.setRange(-1e9, 1e9); input_widget.setDecimals(3)
                if field_def.default_value is not None: input_widget.setValue(float(field_def.default_value))
            
            elif field_def.field_type == FieldType.INTEGER:
                input_widget = QSpinBox(self.props_widget_container)
                input_widget.setRange(-2147483648, 2147483647)
                if field_def.default_value is not None: input_widget.setValue(int(field_def.default_value))
            
            elif field_def.field_type == FieldType.ENUM_STRING:
                input_widget = QComboBox(self.props_widget_container)
                if field_def.enum_values:
                    for enum_val in field_def.enum_values:
                        input_widget.addItem(enum_val)
                if field_def.default_value is not None and field_def.default_value in (field_def.enum_values or []):
                    input_widget.setCurrentText(str(field_def.default_value))
            
            elif field_def.field_type == FieldType.VECTOR2:
                input_widget = QWidget(self.props_widget_container)
                layout = QHBoxLayout(input_widget); layout.setContentsMargins(0,0,0,0)
                x_spin = QDoubleSpinBox(); x_spin.setToolTip("X")
                y_spin = QDoubleSpinBox(); y_spin.setToolTip("Y")
                for s in [x_spin, y_spin]: s.setRange(-1e9, 1e9); s.setDecimals(3)
                if isinstance(field_def.default_value, dict):
                    x_spin.setValue(float(field_def.default_value.get("x",0)))
                    y_spin.setValue(float(field_def.default_value.get("y",0)))
                layout.addWidget(QLabel("X:")); layout.addWidget(x_spin)
                layout.addWidget(QLabel("Y:")); layout.addWidget(y_spin)
                layout.addStretch()
                self._property_value_widgets[f"{field_def.field_name}_x"] = x_spin
                self._property_value_widgets[f"{field_def.field_name}_y"] = y_spin

            elif field_def.field_type == FieldType.VECTOR3:
                input_widget = QWidget(self.props_widget_container)
                layout = QHBoxLayout(input_widget); layout.setContentsMargins(0,0,0,0)
                x_spin = QDoubleSpinBox(); x_spin.setToolTip("X")
                y_spin = QDoubleSpinBox(); y_spin.setToolTip("Y")
                z_spin = QDoubleSpinBox(); z_spin.setToolTip("Z")
                for s in [x_spin, y_spin, z_spin]: s.setRange(-1e9, 1e9); s.setDecimals(3)
                if isinstance(field_def.default_value, dict):
                    x_spin.setValue(float(field_def.default_value.get("x",0)))
                    y_spin.setValue(float(field_def.default_value.get("y",0)))
                    z_spin.setValue(float(field_def.default_value.get("z",0)))
                layout.addWidget(QLabel("X:")); layout.addWidget(x_spin)
                layout.addWidget(QLabel("Y:")); layout.addWidget(y_spin)
                layout.addWidget(QLabel("Z:")); layout.addWidget(z_spin)
                layout.addStretch()
                self._property_value_widgets[f"{field_def.field_name}_x"] = x_spin
                self._property_value_widgets[f"{field_def.field_name}_y"] = y_spin
                self._property_value_widgets[f"{field_def.field_name}_z"] = z_spin

            elif field_def.field_type == FieldType.QUATERNION:
                input_widget = QWidget(self.props_widget_container)
                layout = QHBoxLayout(input_widget); layout.setContentsMargins(0,0,0,0)
                x_spin = QDoubleSpinBox(); x_spin.setToolTip("X")
                y_spin = QDoubleSpinBox(); y_spin.setToolTip("Y")
                z_spin = QDoubleSpinBox(); z_spin.setToolTip("Z")
                w_spin = QDoubleSpinBox(); w_spin.setToolTip("W"); w_spin.setValue(1.0)
                for s in [x_spin,y_spin,z_spin,w_spin]: s.setRange(-1.0,1.0); s.setDecimals(5)
                if isinstance(field_def.default_value, dict):
                    x_spin.setValue(float(field_def.default_value.get("x",0)))
                    y_spin.setValue(float(field_def.default_value.get("y",0)))
                    z_spin.setValue(float(field_def.default_value.get("z",0)))
                    w_spin.setValue(float(field_def.default_value.get("w",1)))
                layout.addWidget(QLabel("X:")); layout.addWidget(x_spin)
                layout.addWidget(QLabel("Y:")); layout.addWidget(y_spin)
                layout.addWidget(QLabel("Z:")); layout.addWidget(z_spin)
                layout.addWidget(QLabel("W:")); layout.addWidget(w_spin)
                layout.addStretch()
                self._property_value_widgets[f"{field_def.field_name}_x"] = x_spin
                self._property_value_widgets[f"{field_def.field_name}_y"] = y_spin
                self._property_value_widgets[f"{field_def.field_name}_z"] = z_spin
                self._property_value_widgets[f"{field_def.field_name}_w"] = w_spin
            
            elif field_def.field_type == FieldType.COLOR_RGBA:
                input_widget = QWidget(self.props_widget_container)
                layout = QHBoxLayout(input_widget); layout.setContentsMargins(0,0,0,0)
                r_spin = QDoubleSpinBox(); r_spin.setToolTip("R"); r_spin.setValue(1.0)
                g_spin = QDoubleSpinBox(); g_spin.setToolTip("G"); g_spin.setValue(1.0)
                b_spin = QDoubleSpinBox(); b_spin.setToolTip("B"); b_spin.setValue(1.0)
                a_spin = QDoubleSpinBox(); a_spin.setToolTip("A"); a_spin.setValue(1.0)
                for s in [r_spin,g_spin,b_spin,a_spin]: s.setRange(0.0,1.0); s.setDecimals(3)
                if isinstance(field_def.default_value, dict):
                    r_spin.setValue(float(field_def.default_value.get("r",1)))
                    g_spin.setValue(float(field_def.default_value.get("g",1)))
                    b_spin.setValue(float(field_def.default_value.get("b",1)))
                    a_spin.setValue(float(field_def.default_value.get("a",1)))
                layout.addWidget(QLabel("R:")); layout.addWidget(r_spin)
                layout.addWidget(QLabel("G:")); layout.addWidget(g_spin)
                layout.addWidget(QLabel("B:")); layout.addWidget(b_spin)
                layout.addWidget(QLabel("A:")); layout.addWidget(a_spin)
                layout.addStretch()
                self._property_value_widgets[f"{field_def.field_name}_r"] = r_spin
                self._property_value_widgets[f"{field_def.field_name}_g"] = g_spin
                self._property_value_widgets[f"{field_def.field_name}_b"] = b_spin
                self._property_value_widgets[f"{field_def.field_name}_a"] = a_spin
            # --- End of Widget Creation ---
            else: 
                input_widget = QLabel(f"[Input for {field_def.field_type.value} not implemented]", self.props_widget_container)

            if input_widget:
                self.props_form_layout.addRow(label_text, input_widget)
                if field_def.field_type not in [FieldType.VECTOR2, FieldType.VECTOR3, FieldType.QUATERNION, FieldType.COLOR_RGBA]:
                    self._property_value_widgets[field_def.field_name] = input_widget

    def _load_data(self, configured_sa: ConfiguredSubAction):
        # --- (Correzioni qui per bloccare segnali e triggerare manualmente _on_sub_action_label_selected) ---
        sub_action_label_to_select = configured_sa.sub_action_label_to_use
        index = self.sub_action_label_combo.findText(sub_action_label_to_select)
        
        self.sub_action_label_combo.blockSignals(True)
        if index != -1:
            self.sub_action_label_combo.setCurrentIndex(index) 
        else:
            QMessageBox.warning(self, "Load Error", f"Could not find SubActionLabel '{sub_action_label_to_select}' in the list.")
            self.sub_action_label_combo.blockSignals(False)
            self._clear_property_widgets_area(add_placeholder_if_no_type=True)
            return 
        self.sub_action_label_combo.blockSignals(False)
        
        # Manually trigger the logic that populates properties based on the (now current) selection
        self._on_sub_action_label_selected(self.sub_action_label_combo.currentIndex())
        # --- Fine correzioni _load_data ---

        if not self._current_selected_sub_action_def: return # Guard clause

        if self._current_selected_sub_action_def.needs_target_item:
            self.item_label_combo.setEnabled(True)
            item_label_to_select = configured_sa.item_label_for_target
            if item_label_to_select:
                item_index = self.item_label_combo.findText(item_label_to_select)
                if item_index != -1:
                    self.item_label_combo.setCurrentIndex(item_index)
                else: 
                    self.item_label_combo.setCurrentIndex(self.item_label_combo.findData(None))
            else: 
                self.item_label_combo.setCurrentIndex(self.item_label_combo.findData(None))
        else:
            self.item_label_combo.setEnabled(False)
            self.item_label_combo.setCurrentIndex(self.item_label_combo.findData(None))

        # --- (Il resto di _load_data per popolare i valori delle proprietà rimane come prima) ---
        for field_name, prop_value in configured_sa.property_values.items():
            field_def_found: Optional[SubActionFieldDefinition] = None
            for fd in self._current_selected_sub_action_def.fields: # Search in the *currently selected* definition's fields
                if fd.field_name == field_name:
                    field_def_found = fd
                    break
            
            if not field_def_found:
                print(f"Warning: Property '{field_name}' from loaded data not found in current SubActionDefinition. Skipping.")
                continue

            if field_def_found.field_type == FieldType.BOOLEAN:
                widget = self._property_value_widgets.get(field_name)
                if isinstance(widget, QCheckBox): widget.setChecked(bool(prop_value))
            elif field_def_found.field_type in [FieldType.STRING, FieldType.ASSET_PATH_STRING, FieldType.ITEM_LABEL_REFERENCE]:
                widget = self._property_value_widgets.get(field_name)
                if isinstance(widget, QLineEdit): widget.setText(str(prop_value))
            elif field_def_found.field_type == FieldType.FLOAT:
                widget = self._property_value_widgets.get(field_name)
                if isinstance(widget, QDoubleSpinBox): widget.setValue(float(prop_value))
            elif field_def_found.field_type == FieldType.INTEGER:
                widget = self._property_value_widgets.get(field_name)
                if isinstance(widget, QSpinBox): widget.setValue(int(prop_value))
            elif field_def_found.field_type == FieldType.ENUM_STRING:
                widget = self._property_value_widgets.get(field_name)
                if isinstance(widget, QComboBox): widget.setCurrentText(str(prop_value))
            elif field_def_found.field_type == FieldType.VECTOR2 and isinstance(prop_value, dict):
                x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y")
                if x_w and isinstance(x_w, QDoubleSpinBox) and y_w and isinstance(y_w, QDoubleSpinBox): 
                    x_w.setValue(float(prop_value.get("x",0))); y_w.setValue(float(prop_value.get("y",0)))
            elif field_def_found.field_type == FieldType.VECTOR3 and isinstance(prop_value, dict):
                x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y"); z_w = self._property_value_widgets.get(f"{field_name}_z")
                if x_w and isinstance(x_w, QDoubleSpinBox) and \
                   y_w and isinstance(y_w, QDoubleSpinBox) and \
                   z_w and isinstance(z_w, QDoubleSpinBox): 
                    x_w.setValue(float(prop_value.get("x",0))); y_w.setValue(float(prop_value.get("y",0))); z_w.setValue(float(prop_value.get("z",0)))
            elif field_def_found.field_type == FieldType.QUATERNION and isinstance(prop_value, dict):
                x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y"); z_w = self._property_value_widgets.get(f"{field_name}_z"); w_w = self._property_value_widgets.get(f"{field_name}_w")
                if x_w and isinstance(x_w, QDoubleSpinBox) and \
                   y_w and isinstance(y_w, QDoubleSpinBox) and \
                   z_w and isinstance(z_w, QDoubleSpinBox) and \
                   w_w and isinstance(w_w, QDoubleSpinBox):
                    x_w.setValue(float(prop_value.get("x",0))); y_w.setValue(float(prop_value.get("y",0))); z_w.setValue(float(prop_value.get("z",0))); w_w.setValue(float(prop_value.get("w",1)))
            elif field_def_found.field_type == FieldType.COLOR_RGBA and isinstance(prop_value, dict):
                r_w = self._property_value_widgets.get(f"{field_name}_r"); g_w = self._property_value_widgets.get(f"{field_name}_g"); b_w = self._property_value_widgets.get(f"{field_name}_b"); a_w = self._property_value_widgets.get(f"{field_name}_a")
                if r_w and isinstance(r_w, QDoubleSpinBox) and \
                   g_w and isinstance(g_w, QDoubleSpinBox) and \
                   b_w and isinstance(b_w, QDoubleSpinBox) and \
                   a_w and isinstance(a_w, QDoubleSpinBox):
                    r_w.setValue(float(prop_value.get("r",1))); g_w.setValue(float(prop_value.get("g",1))); b_w.setValue(float(prop_value.get("b",1))); a_w.setValue(float(prop_value.get("a",1)))


    def get_configured_sub_action(self) -> Optional[ConfiguredSubAction]:
        # (Il codice di get_configured_sub_action con i print DEBUG rimane come nell'artefatto v2)
        # Assicurati che i print DEBUG siano ancora lì per aiutarti a tracciare.
        # Se il problema persiste, l'output di questi print sarà cruciale.
        print("DEBUG: get_configured_sub_action called") 
        selected_sub_action_label_index = self.sub_action_label_combo.currentIndex()
        
        # Check if a valid SubAction Type is selected (not the placeholder)
        if selected_sub_action_label_index < 0 or self.sub_action_label_combo.itemData(selected_sub_action_label_index) is None:
            QMessageBox.warning(self, "Input Error", "Please select a valid SubAction Type.")
            print("DEBUG: No valid SubAction Type selected or itemData is None.") 
            return None
        
        sub_action_label_to_use = self.sub_action_label_combo.currentText()
        current_def: Optional[SubActionDefinition] = self.sub_action_label_combo.itemData(selected_sub_action_label_index)

        if not isinstance(current_def, SubActionDefinition): # More robust check
            QMessageBox.critical(self, "Internal Error", f"Could not retrieve a valid definition for {sub_action_label_to_use}.")
            print(f"DEBUG: Definition for {sub_action_label_to_use} is not a SubActionDefinition instance.") 
            return None

        item_label_for_target: Optional[str] = None
        if current_def.needs_target_item:
            selected_item_label_data = self.item_label_combo.currentData()
            if selected_item_label_data is not None: 
                item_label_for_target = str(selected_item_label_data)
            else: 
                QMessageBox.warning(self, "Input Error", f"SubAction '{sub_action_label_to_use}' requires a Target ItemLabel.")
                print(f"DEBUG: Target ItemLabel required but not selected for {sub_action_label_to_use}") 
                return None
        
        property_values: Dict[str, Any] = {}
        print(f"DEBUG: Processing fields for {sub_action_label_to_use}: {len(current_def.fields)} fields") 
        for field_def in current_def.fields:
            field_name = field_def.field_name
            value: Any = None 
            print(f"DEBUG:  Processing field: {field_name} (Type: {field_def.field_type})") 
            try:
                if field_def.field_type == FieldType.BOOLEAN:
                    widget = self._property_value_widgets.get(field_name)
                    if isinstance(widget, QCheckBox): value = widget.isChecked()
                    else: print(f"DEBUG: Widget for BOOLEAN field '{field_name}' is not QCheckBox or not found. Widget: {widget}") 
                elif field_def.field_type in [FieldType.STRING, FieldType.ASSET_PATH_STRING, FieldType.ITEM_LABEL_REFERENCE]:
                    widget = self._property_value_widgets.get(field_name)
                    if isinstance(widget, QLineEdit): value = widget.text() 
                    else: print(f"DEBUG: Widget for STRING-like field '{field_name}' is not QLineEdit or not found. Widget: {widget}") 
                elif field_def.field_type == FieldType.FLOAT:
                    widget = self._property_value_widgets.get(field_name)
                    if isinstance(widget, QDoubleSpinBox): value = widget.value()
                    else: print(f"DEBUG: Widget for FLOAT field '{field_name}' is not QDoubleSpinBox or not found. Widget: {widget}") 
                elif field_def.field_type == FieldType.INTEGER:
                    widget = self._property_value_widgets.get(field_name)
                    if isinstance(widget, QSpinBox): value = widget.value()
                    else: print(f"DEBUG: Widget for INTEGER field '{field_name}' is not QSpinBox or not found. Widget: {widget}") 
                elif field_def.field_type == FieldType.ENUM_STRING:
                    widget = self._property_value_widgets.get(field_name)
                    if isinstance(widget, QComboBox): value = widget.currentText()
                    else: print(f"DEBUG: Widget for ENUM_STRING field '{field_name}' is not QComboBox or not found. Widget: {widget}") 
                elif field_def.field_type == FieldType.VECTOR2:
                    x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y")
                    if isinstance(x_w, QDoubleSpinBox) and isinstance(y_w, QDoubleSpinBox): value = {"x": x_w.value(), "y": y_w.value()}
                    else: print(f"DEBUG: Widgets for Vector2 {field_name} not found or wrong type. X: {x_w}, Y: {y_w}") 
                elif field_def.field_type == FieldType.VECTOR3:
                    x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y"); z_w = self._property_value_widgets.get(f"{field_name}_z")
                    if isinstance(x_w, QDoubleSpinBox) and isinstance(y_w, QDoubleSpinBox) and isinstance(z_w, QDoubleSpinBox): value = {"x": x_w.value(), "y": y_w.value(), "z": z_w.value()}
                    else: print(f"DEBUG: Widgets for Vector3 {field_name} not found or wrong type. X: {x_w}, Y: {y_w}, Z: {z_w}") 
                elif field_def.field_type == FieldType.QUATERNION:
                    x_w = self._property_value_widgets.get(f"{field_name}_x"); y_w = self._property_value_widgets.get(f"{field_name}_y"); z_w = self._property_value_widgets.get(f"{field_name}_z"); w_w = self._property_value_widgets.get(f"{field_name}_w")
                    if isinstance(x_w, QDoubleSpinBox) and isinstance(y_w, QDoubleSpinBox) and isinstance(z_w, QDoubleSpinBox) and isinstance(w_w, QDoubleSpinBox): value = {"x": x_w.value(), "y": y_w.value(), "z": z_w.value(), "w": w_w.value()}
                    else: print(f"DEBUG: Widgets for Quaternion {field_name} not found or wrong type.") 
                elif field_def.field_type == FieldType.COLOR_RGBA:
                    r_w = self._property_value_widgets.get(f"{field_name}_r"); g_w = self._property_value_widgets.get(f"{field_name}_g"); b_w = self._property_value_widgets.get(f"{field_name}_b"); a_w = self._property_value_widgets.get(f"{field_name}_a")
                    if isinstance(r_w, QDoubleSpinBox) and isinstance(g_w, QDoubleSpinBox) and isinstance(b_w, QDoubleSpinBox) and isinstance(a_w, QDoubleSpinBox): value = {"r": r_w.value(), "g": g_w.value(), "b": b_w.value(), "a": a_w.value()}
                    else: print(f"DEBUG: Widgets for ColorRGBA {field_name} not found or wrong type.") 
                else:
                    print(f"Warning: Unhandled FieldType '{field_def.field_type}' when getting property value for '{field_name}'.")
                    continue 
                
                property_values[field_name] = value
                print(f"DEBUG:   Got value for {field_name}: {value} (type: {type(value)})") 

            except KeyError as ke:
                QMessageBox.critical(self, "Internal Error", f"Widget for property '{field_name}' (KeyError: {ke}) not found. Please report this bug.")
                print(f"DEBUG: KeyError for {field_name}: {ke}") 
                return None
            except Exception as e:
                QMessageBox.critical(self, "Input Error", f"Error retrieving value for property '{field_name}': {e}")
                print(f"DEBUG: Exception for {field_name}: {e}") 
                return None
        
        print(f"DEBUG: Final property_values: {property_values}") 
        try:
            csa_instance = ConfiguredSubAction(
                sub_action_label_to_use=sub_action_label_to_use,
                item_label_for_target=item_label_for_target,
                property_values=property_values
            )
            print(f"DEBUG: ConfiguredSubAction instance created: {csa_instance.to_dict()}") 
            return csa_instance
        except Exception as e:
            QMessageBox.critical(self, "Creation Error", f"Could not create ConfiguredSubAction: {e}")
            print(f"DEBUG: Error creating ConfiguredSubAction: {e}") 
            return None

    def accept(self):
        print("DEBUG: Accept called in ConfiguredSubActionDialog") 
        csa = self.get_configured_sub_action()
        if csa is not None:
            print("DEBUG: get_configured_sub_action returned an object. Calling super().accept()") 
            super().accept()
        else:
            print("DEBUG: get_configured_sub_action returned None. Dialog not accepted.") 

# --- Standalone Test ---
# (Standalone test code ommitted for brevity, keep previous version if needed)
# (Ensure bootstrap for sys.path is at the very top if running this file directly)
if __name__ == '__main__':
    # Bootstrap for standalone execution
    import sys
    import os
    if __name__ == '__main__' and __package__ is None: # Check __package__ as well
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_script_dir)
        framework_tool_dir = os.path.dirname(gui_dir)
        project_root_dir = os.path.dirname(framework_tool_dir)
        if project_root_dir not in sys.path:
            sys.path.insert(0, project_root_dir)

    from PySide6.QtWidgets import QApplication
    from framework_tool.data_models.project_data import ProjectData as TestProjectData
    from framework_tool.data_models.sub_action_definition import SubActionDefinition as TestSubActionDef, SubActionFieldDefinition as TestFieldDef
    from framework_tool.data_models.common_types import FieldType as TestFieldType
    from framework_tool.data_models.action_definition import ConfiguredSubAction as TestConfiguredSA

    app = QApplication(sys.argv)
    dummy_project = TestProjectData()
    dummy_project.item_labels = ["Door_A", "Key_Card_Reader", "Emergency_Button"]
    sad1_fields = [TestFieldDef("isEnabled", TestFieldType.BOOLEAN, default_value=True), TestFieldDef("message", TestFieldType.STRING, default_value="Activated!")]
    sad1 = TestSubActionDef(description="Activates a device.", needs_target_item=True, fields=sad1_fields)
    dummy_project.sub_action_labels.append("ActivateDevice")
    dummy_project.sub_action_definitions["ActivateDevice"] = sad1
    sad2_fields = [TestFieldDef("animationName", TestFieldType.STRING), TestFieldDef("speedMultiplier", TestFieldType.FLOAT, default_value=1.0)]
    sad2 = TestSubActionDef(description="Plays an animation on an object.", needs_target_item=True, fields=sad2_fields)
    dummy_project.sub_action_labels.append("PlayObjectAnimation")
    dummy_project.sub_action_definitions["PlayObjectAnimation"] = sad2
    sad3_fields = [TestFieldDef("targetPosition", TestFieldType.VECTOR3, default_value={"x":0,"y":0,"z":0}), TestFieldDef("duration", TestFieldType.FLOAT, default_value=1.0)]
    sad3 = TestSubActionDef(description="Moves an object.", needs_target_item=True, fields=sad3_fields)
    dummy_project.sub_action_labels.append("MoveTo")
    dummy_project.sub_action_definitions["MoveTo"] = sad3

    print("Test 1: Adding a new ConfiguredSubAction")
    add_dialog = ConfiguredSubActionDialog(project_data=dummy_project)
    if add_dialog.exec() == QDialog.DialogCode.Accepted:
        new_csa = add_dialog.get_configured_sub_action()
        if new_csa:
            print("New ConfiguredSubAction created:")
            print(f"  SubActionLabel: {new_csa.sub_action_label_to_use}")
            print(f"  ItemLabel Target: {new_csa.item_label_for_target}")
            print(f"  PropertyValues: {new_csa.property_values}")
            print("-" * 20)
    else:
        print("Add new ConfiguredSubAction dialog cancelled.")
    # ... (Rest of the test code) ...
