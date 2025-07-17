# framework_tool/gui/widgets/action_instance_customizer_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QGroupBox, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox,
    QDoubleSpinBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List, Dict, Any

from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.session_graph import ActionNode
from framework_tool.data_models.action_definition import ActionDefinition
from framework_tool.data_models.custom_field_definition import CustomFieldDefinition

from ..dialogs.field_edit_dialog import FieldEditDialog


class ActionInstanceCustomizerWidget(QWidget):
    """
    Allows customization of a selected ActionNode instance.
    This includes setting instance label and custom field values.
    """
    instance_changed = Signal()
    
    def __init__(self, project_data_ref: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data_ref = project_data_ref
        self._current_action_node: Optional[ActionNode] = None
        self._current_action_definition: Optional[ActionDefinition] = None
        
        self._init_ui()
        self.clear_details()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Action Node Info (read-only)
        node_info_group = QGroupBox("Action Instance Info", self)
        node_info_layout = QFormLayout(node_info_group)
        
        self.action_label_display = QLineEdit(self)
        self.action_label_display.setReadOnly(True)
        node_info_layout.addRow("Action Label:", self.action_label_display)
        
        self.node_id_display = QLineEdit(self)
        self.node_id_display.setReadOnly(True)
        node_info_layout.addRow("Node ID:", self.node_id_display)
        
        main_layout.addWidget(node_info_group)
        
        # Instance Customization (editable)
        customization_group = QGroupBox("Instance Customization", self)
        customization_layout = QVBoxLayout(customization_group)
        
        # Instance Label
        instance_label_layout = QFormLayout()
        self.instance_label_edit = QLineEdit(self)
        self.instance_label_edit.setPlaceholderText("Optional custom label for this instance...")
        self.instance_label_edit.textChanged.connect(self._on_instance_label_changed)
        instance_label_layout.addRow("Instance Label:", self.instance_label_edit)
        customization_layout.addLayout(instance_label_layout)
        
        # Custom Fields Table
        customization_layout.addWidget(QLabel("Custom Field Values:"))
        
        self.custom_fields_table = QTableWidget(self)
        self.custom_fields_table.setColumnCount(3)
        self.custom_fields_table.setHorizontalHeaderLabels(["Field Name", "Type", "Value"])
        self.custom_fields_table.horizontalHeader().setStretchLastSection(True)
        self.custom_fields_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        customization_layout.addWidget(self.custom_fields_table)
        
        main_layout.addWidget(customization_group)
        
        # Action Definition Details (read-only)
        definition_group = QGroupBox("Action Definition Details", self)
        definition_layout = QFormLayout(definition_group)
        
        self.autocomplete_display = QCheckBox("Autocomplete")
        self.autocomplete_display.setEnabled(False)  # Read-only
        definition_layout.addWidget(self.autocomplete_display)
        
        self.description_display = QTextEdit(self)
        self.description_display.setReadOnly(True)
        self.description_display.setFixedHeight(60)
        definition_layout.addRow("Description:", self.description_display)
        
        main_layout.addWidget(definition_group)
        main_layout.addStretch()
    
    def load_action_node_details(self, action_node: Optional[ActionNode]):
        """Loads and displays details for the given ActionNode."""
        self._current_action_node = action_node
        
        if not action_node or not self.project_data_ref:
            self.clear_details()
            return
        
        # Display basic node info
        self.action_label_display.setText(action_node.action_label_to_execute)
        self.node_id_display.setText(action_node.node_id)
        
        # Display instance customization
        self.instance_label_edit.blockSignals(True)
        self.instance_label_edit.setText(action_node.instance_label)
        self.instance_label_edit.blockSignals(False)
        
        # Get action definition
        self._current_action_definition = self.project_data_ref.action_definitions.get(
            action_node.action_label_to_execute
        )
        
        if self._current_action_definition:
            self.autocomplete_display.setChecked(self._current_action_definition.autocomplete)
            self.description_display.setText(self._current_action_definition.description or "N/A")
            self._populate_custom_fields_table()
        else:
            self.autocomplete_display.setChecked(False)
            self.description_display.setText("[Definition Not Found]")
            self.custom_fields_table.setRowCount(0)
        
        self._enable_editing(True)
    
    def _populate_custom_fields_table(self):
        """Populate the custom fields table with action definition fields and current values."""
        if not self._current_action_definition or not self._current_action_node:
            self.custom_fields_table.setRowCount(0)
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
            
            # Create appropriate widget for value column
            current_value = self._current_action_node.custom_field_values.get(field.field_name, field.get_default_value_for_type())
            widget = self._create_value_widget(field, current_value, row)
            self.custom_fields_table.setCellWidget(row, 2, widget)
            
            # Store the field definition in the row
            name_item.setData(Qt.ItemDataRole.UserRole, field)
    
    def _create_value_widget(self, field, current_value, row):
        """Create appropriate widget for editing field value."""
        from framework_tool.data_models.common_types import FieldType
        
        if field.field_type == FieldType.BOOLEAN:
            widget = QCheckBox()
            widget.setChecked(bool(current_value) if current_value is not None else False)
            widget.toggled.connect(lambda checked: self._on_value_changed(row, checked))
            return widget
            
        elif field.field_type == FieldType.STRING:
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda text: self._on_value_changed(row, text))
            return widget
            
        elif field.field_type == FieldType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(-999999.99, 999999.99)
            widget.setDecimals(3)
            widget.setValue(float(current_value) if current_value is not None else 0.0)
            widget.valueChanged.connect(lambda value: self._on_value_changed(row, value))
            return widget
            
        elif field.field_type == FieldType.INTEGER:
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(current_value) if current_value is not None else 0)
            widget.valueChanged.connect(lambda value: self._on_value_changed(row, value))
            return widget
            
        elif field.field_type == FieldType.ENUM_STRING:
            widget = QComboBox()
            if field.enum_values:
                for enum_val in field.enum_values:
                    widget.addItem(enum_val)
                if current_value and current_value in field.enum_values:
                    widget.setCurrentText(current_value)
            widget.currentTextChanged.connect(lambda text: self._on_value_changed(row, text))
            return widget
            
        elif field.field_type == FieldType.ITEM_LABEL_REFERENCE:
            widget = QComboBox()
            widget.addItem("[Not Set]", "")
            if self.project_data_ref and hasattr(self.project_data_ref, 'item_labels'):
                for label in sorted(self.project_data_ref.item_labels):
                    widget.addItem(label, label)
                if current_value:
                    index = widget.findData(current_value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
            widget.currentIndexChanged.connect(lambda index: self._on_value_changed(row, widget.currentData() if widget.currentData() != "" else None))
            return widget
            
        elif field.field_type == FieldType.VECTOR2:
            return self._create_vector_widget(current_value, ["x", "y"], row)
            
        elif field.field_type == FieldType.VECTOR3:
            return self._create_vector_widget(current_value, ["x", "y", "z"], row)
            
        elif field.field_type == FieldType.RGBA:
            return self._create_vector_widget(current_value, ["r", "g", "b", "a"], row, is_color=True)
        
        # Fallback to text
        widget = QLineEdit()
        widget.setText(str(current_value) if current_value is not None else "")
        widget.textChanged.connect(lambda text: self._on_value_changed(row, text))
        return widget
    
    def _create_vector_widget(self, current_value, components, row, is_color=False):
        """Create widget for vector types (Vector2, Vector3, RGBA)."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        spin_boxes = {}
        for component in components:
            layout.addWidget(QLabel(f"{component.upper()}:"))
            spin_box = QDoubleSpinBox()
            if is_color:  # RGBA values 0-1
                spin_box.setRange(0.0, 1.0)
                spin_box.setDecimals(3)
                spin_box.setSingleStep(0.1)
            else:  # Vector values
                spin_box.setRange(-999999.99, 999999.99)
                spin_box.setDecimals(2)
            
            # Set current value
            if isinstance(current_value, dict) and component in current_value:
                spin_box.setValue(float(current_value[component]))
            else:
                spin_box.setValue(1.0 if is_color and component == "a" else 0.0)
            
            spin_box.valueChanged.connect(lambda: self._on_vector_changed(row, components, spin_boxes))
            spin_boxes[component] = spin_box
            layout.addWidget(spin_box)
        
        # Store spinboxes for later access
        container.spin_boxes = spin_boxes
        return container
    
    def _on_vector_changed(self, row, components, spin_boxes):
        """Handle vector component change."""
        value = {comp: spin_boxes[comp].value() for comp in components}
        self._on_value_changed(row, value)
    
    def _on_value_changed(self, row, value):
        """Handle when a field value changes."""
        if not self._current_action_node:
            return
            
        # Get field definition
        field_def = self.custom_fields_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if field_def:
            # Update the action node
            self._current_action_node.custom_field_values[field_def.field_name] = value
            self.instance_changed.emit()
    
    def _format_field_value(self, value: Any, field_type: str) -> str:
        """Format field value for display."""
        if value is None:
            return "[Not Set]"
        
        if field_type == "float":
            return f"{value:.2f}"
        elif field_type == "bool":
            return "True" if value else "False"
        elif field_type in ["Vector2", "Vector3", "RGBA"]:
            if isinstance(value, dict):
                parts = [f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}" 
                        for k, v in value.items()]
                return f"{{{', '.join(parts)}}}"
        
        return str(value)
    
    
    def _on_instance_label_changed(self, text: str):
        """Handle instance label change."""
        if self._current_action_node:
            self._current_action_node.instance_label = text
            self.instance_changed.emit()
    
    def _enable_editing(self, enabled: bool):
        """Enable or disable editing controls."""
        self.instance_label_edit.setEnabled(enabled)
        self.custom_fields_table.setEnabled(enabled)
    
    def clear_details(self):
        """Clear all displayed details."""
        self.action_label_display.clear()
        self.node_id_display.clear()
        self.instance_label_edit.clear()
        self.autocomplete_display.setChecked(False)
        self.description_display.clear()
        self.custom_fields_table.setRowCount(0)
        self._current_action_node = None
        self._current_action_definition = None
        self._enable_editing(False)