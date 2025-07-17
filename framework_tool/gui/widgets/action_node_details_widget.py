# framework_tool/gui/widgets/action_node_details_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QListWidget, QListWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt
from typing import Optional, List # <<<--- List AGGIUNTO QUI

from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.session_graph import ActionNode
from framework_tool.data_models.action_definition import ActionDefinition, ConfiguredSubAction

class ActionNodeDetailsWidget(QWidget):
    """
    Displays details of a selected ActionNode and its corresponding ActionDefinition.
    This widget is read-only.
    """
    def __init__(self, project_data_ref: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data_ref = project_data_ref
        self._current_action_node: Optional[ActionNode] = None
        self._current_action_definition: Optional[ActionDefinition] = None

        self._init_ui()
        self.clear_details() # Start empty

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5)

        # --- Action Node Info ---
        node_info_group = QGroupBox("Selected Action Node", self)
        node_info_layout = QFormLayout(node_info_group)

        self.action_label_display = QLineEdit(self)
        self.action_label_display.setReadOnly(True)
        node_info_layout.addRow("ActionLabel:", self.action_label_display)

        self.node_id_display = QLineEdit(self)
        self.node_id_display.setReadOnly(True)
        node_info_layout.addRow("Node ID:", self.node_id_display)
        
        main_layout.addWidget(node_info_group)

        # --- Action Definition Info ---
        action_def_group = QGroupBox("Action Definition Details", self)
        action_def_layout = QFormLayout(action_def_group)

        self.help_label_display = QLineEdit(self)
        self.help_label_display.setReadOnly(True)
        action_def_layout.addRow("Help Label:", self.help_label_display)

        self.description_display = QTextEdit(self)
        self.description_display.setReadOnly(True)
        self.description_display.setFixedHeight(80) 
        action_def_layout.addRow("Description:", self.description_display)
        
        main_layout.addWidget(action_def_group)

        # --- Configured SubActions List ---
        sub_actions_group = QGroupBox("Configured SubActions (from Definition)", self)
        sub_actions_layout = QVBoxLayout(sub_actions_group)
        
        self.sub_actions_list_widget = QListWidget(self)
        sub_actions_layout.addWidget(self.sub_actions_list_widget)
        
        main_layout.addWidget(sub_actions_group)
        main_layout.addStretch() 
        self.setLayout(main_layout)

    def load_action_node_details(self, action_node: Optional[ActionNode]):
        """Loads and displays details for the given ActionNode."""
        self._current_action_node = action_node
        
        if not action_node:
            self.clear_details()
            return

        self.action_label_display.setText(action_node.action_label_to_execute)
        self.node_id_display.setText(action_node.node_id)

        self._current_action_definition = self.project_data_ref.action_definitions.get(
            action_node.action_label_to_execute
        )

        if self._current_action_definition:
            self.help_label_display.setText(self._current_action_definition.help_label or "N/A")
            self.description_display.setText(self._current_action_definition.description or "N/A")
            self._populate_sub_actions_list(self._current_action_definition.sub_actions)
        else:
            self.help_label_display.setText("[Definition Not Found]")
            self.description_display.setText("[Definition Not Found]")
            self.sub_actions_list_widget.clear()
            self.sub_actions_list_widget.addItem("ActionDefinition not found for this ActionLabel.")

    def _populate_sub_actions_list(self, configured_sub_actions: List[ConfiguredSubAction]): # List is now defined
        self.sub_actions_list_widget.clear()
        if not configured_sub_actions:
            self.sub_actions_list_widget.addItem("No SubActions configured for this Action.")
            return

        for i, csa in enumerate(configured_sub_actions):
            item_text = f"{i+1}. {csa.sub_action_label_to_use}"
            
            target_text = ""
            if csa.item_label_for_target:
                target_text = f" (Target: {csa.item_label_for_target})"
            
            props_list = []
            if csa.property_values:
                for key, val in csa.property_values.items():
                    # Basic string representation for properties
                    val_str = str(val)
                    if isinstance(val, float):
                        val_str = f"{val:.2f}" # Format float
                    elif isinstance(val, dict): # For Vector, Color, etc.
                        val_str = ", ".join([f"{k_v}:{v_v}" for k_v, v_v in val.items()])
                    props_list.append(f"{key}: {val_str}")
            props_text = ""
            if props_list:
                props_text = f" | Props: {'; '.join(props_list)}" # Use semicolon for better readability
            
            list_item = QListWidgetItem(f"{item_text}{target_text}{props_text}")
            self.sub_actions_list_widget.addItem(list_item)


    def clear_details(self):
        """Clears all displayed details."""
        self.action_label_display.clear()
        self.node_id_display.clear()
        self.help_label_display.clear()
        self.description_display.clear()
        self.sub_actions_list_widget.clear()
        self.sub_actions_list_widget.addItem("[No Action Node selected]")
        self._current_action_node = None
        self._current_action_definition = None
