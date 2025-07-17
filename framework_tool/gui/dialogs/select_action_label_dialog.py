# framework_tool/gui/dialogs/select_action_label_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLineEdit, QHBoxLayout, QLabel,
    QWidget # <<<--- QWidget AGGIUNTO QUI
)
from PySide6.QtCore import Qt, Slot
from typing import Optional, List, Dict # Added Dict

from framework_tool.data_models.action_definition import ActionDefinition # For type hinting if needed


class SelectActionLabelDialog(QDialog):
    """
    A simple dialog to select an ActionLabel from a list of available ActionDefinitions.
    """
    def __init__(self, 
                 action_definitions: Dict[str, ActionDefinition], 
                 parent: Optional[QWidget] = None): # QWidget is now defined
        super().__init__(parent)
        self.action_definitions = action_definitions
        self.selected_action_label: Optional[str] = None

        self.setWindowTitle("Select Action Type")
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)

        self._init_ui()
        self._populate_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:", self))
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter action labels...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)
        main_layout.addLayout(filter_layout)

        self.list_widget = QListWidget(self)
        self.list_widget.setSortingEnabled(True)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if self.ok_button: 
             self.ok_button.setEnabled(False)
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)

        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def _populate_list(self):
        self.list_widget.clear()
        action_labels = sorted(self.action_definitions.keys())
        for label in action_labels:
            action_def = self.action_definitions.get(label)
            item_text = label
            if action_def and action_def.description:
                desc_summary = action_def.description.split('\n')[0]
                if len(desc_summary) > 40: desc_summary = desc_summary[:37] + "..."
                item_text = f"{label} ({desc_summary})"

            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, label) 
            self.list_widget.addItem(list_item)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0) 

    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selection_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if self.ok_button:
            self.ok_button.setEnabled(current is not None)

    @Slot(QListWidgetItem)
    def _on_item_double_clicked(self, item: QListWidgetItem):
        if item: 
            self.accept()

    @Slot(str)
    def _apply_filter(self, filter_text: str):
        filter_text_lower = filter_text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                item_text_lower = item.text().lower()
                item.setHidden(filter_text_lower not in item_text_lower)

    def accept(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_action_label = current_item.data(Qt.ItemDataRole.UserRole) 
            super().accept()
        else:
            super().reject() 

    @staticmethod
    def get_selected_action_label(action_definitions: Dict[str, ActionDefinition], 
                                  parent: Optional[QWidget] = None) -> Optional[str]:
        dialog = SelectActionLabelDialog(action_definitions, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted: # QDialog.DialogCode should be fine here
            return dialog.selected_action_label
        return None

# --- Standalone Test (Optional) ---
if __name__ == '__main__':
    import sys
    import os
    if __name__ == '__main__' and __package__ is None:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_script_dir)
        framework_tool_dir = os.path.dirname(gui_dir)
        project_root_dir = os.path.dirname(framework_tool_dir)
        if project_root_dir not in sys.path:
            sys.path.insert(0, project_root_dir)

    from PySide6.QtWidgets import QApplication # Moved here for standalone
    from framework_tool.data_models.action_definition import ActionDefinition as TestActionDef

    app = QApplication(sys.argv)
    
    test_action_defs = {
        "OpenDoor": TestActionDef(help_label="Opens a door."),
        "CloseDoor": TestActionDef(description="Closes a specific door."),
        "PickupItem": TestActionDef(help_label="Picks up an item."),
        "UseItem": TestActionDef(description="Uses a held item on a target.")
    }

    selected_label = SelectActionLabelDialog.get_selected_action_label(test_action_defs)
    if selected_label:
        print(f"Selected ActionLabel: {selected_label}")
    else:
        print("No ActionLabel selected or dialog cancelled.")
