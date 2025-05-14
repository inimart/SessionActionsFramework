# framework_tool/gui/widgets/label_editor_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import List, Callable, Optional

class LabelEditorWidget(QWidget):
    """
    A reusable widget for editing a list of string labels.
    Provides functionalities for adding, removing, editing, filtering,
    and displaying labels.
    """

    # Signal emitted when the list of labels has been modified by this widget.
    # The main window can connect to this to mark the project as dirty.
    labels_changed = Signal()

    def __init__(self,
                 widget_title: str = "Edit Labels",
                 get_labels_func: Optional[Callable[[], List[str]]] = None,
                 set_labels_func: Optional[Callable[[List[str]], None]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(widget_title)

        if get_labels_func is None or set_labels_func is None:
            # Fallback to internal list if no external functions are provided (for standalone testing)
            self._internal_labels: List[str] = []
            self.get_labels = lambda: self._internal_labels
            self.set_labels = lambda new_list: setattr(self, '_internal_labels', new_list)
            print(f"Warning: LabelEditorWidget '{widget_title}' using internal list due to missing get/set functions.")
        else:
            self.get_labels = get_labels_func
            self.set_labels = set_labels_func
        
        self._init_ui()
        self.load_labels()

    def _init_ui(self):
        """Initializes the User Interface for the widget."""
        main_layout = QVBoxLayout(self)

        # --- Filter ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:", self))
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter labels...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)
        main_layout.addLayout(filter_layout)

        # --- List Widget ---
        self.list_widget = QListWidget(self)
        self.list_widget.setSortingEnabled(True) # Automatically sorts items
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self._edit_selected_item_action)
        main_layout.addWidget(self.list_widget)

        # --- Add New Label ---
        add_layout = QHBoxLayout()
        self.add_label_input = QLineEdit(self)
        self.add_label_input.setPlaceholderText("Enter new label name")
        self.add_label_input.returnPressed.connect(self._add_label_action) # Add on Enter key
        add_layout.addWidget(self.add_label_input)
        
        add_button = QPushButton("Add Label", self)
        add_button.clicked.connect(self._add_label_action)
        add_layout.addWidget(add_button)
        main_layout.addLayout(add_layout)

        # --- Action Buttons (Edit, Remove) ---
        action_buttons_layout = QHBoxLayout()
        edit_button = QPushButton("Edit Selected", self)
        edit_button.clicked.connect(self._edit_selected_item_action)
        action_buttons_layout.addWidget(edit_button)

        remove_button = QPushButton("Remove Selected", self)
        remove_button.clicked.connect(self._remove_selected_item_action)
        action_buttons_layout.addWidget(remove_button)
        
        action_buttons_layout.addStretch() # Push buttons to the left
        main_layout.addLayout(action_buttons_layout)

    def load_labels(self):
        """Loads labels from the source and populates the list widget."""
        self.list_widget.clear()
        current_labels = self.get_labels() # Get from ProjectData via callback
        for label_text in sorted(current_labels): # Ensure initial sort if list_widget sort is off
            item = QListWidgetItem(label_text)
            self.list_widget.addItem(item)
        # Apply current filter based on the text in the filter input field
        self._apply_filter(self.filter_input.text()) # <<<--- CORREZIONE APPLICATA QUI

    def _save_labels_to_source(self, updated_labels: List[str]):
        """Saves the updated list of labels back to the source and emits signal."""
        self.set_labels(sorted(list(set(updated_labels)))) # Ensure unique and sorted
        self.labels_changed.emit()
        self.load_labels() # Reload to reflect changes, sorting, and filtering

    @Slot()
    def _add_label_action(self):
        """Adds a new label from the input field."""
        new_label_text = self.add_label_input.text().strip()
        if not new_label_text:
            QMessageBox.warning(self, "Input Error", "Label name cannot be empty.")
            return

        current_labels = self.get_labels()
        # Case-insensitive check for duplicates before adding
        if any(new_label_text.lower() == label.lower() for label in current_labels):
            QMessageBox.warning(self, "Duplicate Label", f"The label '{new_label_text}' already exists (case-insensitive).")
            return

        updated_labels = current_labels + [new_label_text]
        self._save_labels_to_source(updated_labels)
        
        self.add_label_input.clear()
        # Optionally, select the newly added item
        items = self.list_widget.findItems(new_label_text, Qt.MatchFlag.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])

    @Slot()
    def _edit_selected_item_action(self):
        """Edits the currently selected label in the list."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a label to edit.")
            return
        
        current_item = selected_items[0]
        original_label_text = current_item.text()

        new_label_text, ok = QInputDialog.getText(
            self, 
            "Edit Label", 
            "Enter new name for the label:", 
            QLineEdit.EchoMode.Normal, 
            original_label_text
        )

        if ok and new_label_text:
            new_label_text = new_label_text.strip()
            if not new_label_text:
                QMessageBox.warning(self, "Input Error", "Label name cannot be empty.")
                return

            if new_label_text.lower() == original_label_text.lower():
                if new_label_text != original_label_text: # Case only change
                    pass 
                else: # No change at all
                    return

            current_labels = self.get_labels()
            if any(new_label_text.lower() == label.lower() and label.lower() != original_label_text.lower() 
                   for label in current_labels):
                QMessageBox.warning(self, "Duplicate Label", f"The label '{new_label_text}' already exists or conflicts with another label (case-insensitive).")
                return
            try:
                idx = current_labels.index(original_label_text) 
                updated_labels = list(current_labels) 
                updated_labels[idx] = new_label_text
                self._save_labels_to_source(updated_labels)
            except ValueError:
                QMessageBox.critical(self, "Error", "Could not find the original label in the source list. Please reload.")
        elif ok and not new_label_text: 
             QMessageBox.warning(self, "Input Error", "Label name cannot be empty.")

    @Slot()
    def _remove_selected_item_action(self):
        """Removes the currently selected label from the list."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a label to remove.")
            return

        label_to_remove = selected_items[0].text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the label '{label_to_remove}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            current_labels = self.get_labels()
            updated_labels = [label for label in current_labels if label != label_to_remove]
            self._save_labels_to_source(updated_labels)

    @Slot(str)
    def _apply_filter(self, filter_text: str): # Signature is correct for a slot connected to textChanged
        """Filters the items in the list widget based on the filter text."""
        filter_text_lower = filter_text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                item_text_lower = item.text().lower()
                item.setHidden(filter_text_lower not in item_text_lower)

# --- Standalone Test for LabelEditorWidget (optional) ---
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication, QDialog # QApplication moved here for test

    app = QApplication(sys.argv)
    
    dialog = QDialog()
    dialog.setWindowTitle("Label Editor Test")
    # Layout for the dialog needs to be set on the dialog itself
    # layout = QVBoxLayout(dialog) # This was correct

    test_labels_data = ["Apple", "Banana", "Cherry", "Date", "Elderberry"] # Renamed to avoid conflict

    def get_test_labels() -> List[str]:
        print("get_test_labels called")
        return test_labels_data

    def set_test_labels(new_list: List[str]):
        print(f"set_test_labels called with: {new_list}")
        global test_labels_data
        test_labels_data = new_list


    editor_widget = LabelEditorWidget(
        widget_title="Fruit Labels", # This sets the widget's window title, not the dialog's
        get_labels_func=get_test_labels,
        set_labels_func=set_test_labels,
        parent=dialog # Set the dialog as parent
    )
    
    def on_labels_changed_test():
        print("Test: labels_changed signal received! Current labels:", get_test_labels())

    editor_widget.labels_changed.connect(on_labels_changed_test)
    
    # Add the editor_widget to the dialog's layout
    dialog_layout = QVBoxLayout() # Create a layout for the dialog
    dialog_layout.addWidget(editor_widget)
    dialog.setLayout(dialog_layout) # Set this layout on the dialog

    dialog.resize(400, 300)
    dialog.show()
    
    sys.exit(app.exec())