# framework_tool/gui/dialogs/field_edit_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import QInputDialog, QMessageBox
from typing import Any


class FieldEditDialog:
    """
    Simple dialog utility for editing field values.
    """
    
    @staticmethod
    def edit_field_value(field_name: str, field_type, current_value: Any, parent=None) -> Any:
        """
        Static method to edit a field value using a simple dialog.
        Returns the new value or None if cancelled.
        """
        # Convert FieldType enum to string if needed
        if hasattr(field_type, 'value'):
            field_type_str = field_type.value
        else:
            field_type_str = str(field_type)
        
        if field_type_str == "string":
            text, ok = QInputDialog.getText(
                parent, 
                f"Edit {field_name}", 
                f"Enter value for {field_name}:",
                text=str(current_value) if current_value is not None else ""
            )
            return text if ok else None
            
        elif field_type_str == "float":
            value, ok = QInputDialog.getDouble(
                parent,
                f"Edit {field_name}",
                f"Enter value for {field_name}:",
                value=float(current_value) if current_value is not None else 0.0,
                decimals=2
            )
            return value if ok else None
            
        elif field_type_str == "integer":
            value, ok = QInputDialog.getInt(
                parent,
                f"Edit {field_name}",
                f"Enter value for {field_name}:",
                value=int(current_value) if current_value is not None else 0
            )
            return value if ok else None
            
        elif field_type_str == "boolean":
            items = ["True", "False"]
            current_text = "True" if current_value else "False"
            text, ok = QInputDialog.getItem(
                parent,
                f"Edit {field_name}",
                f"Select value for {field_name}:",
                items,
                current=items.index(current_text) if current_text in items else 0,
                editable=False
            )
            return text == "True" if ok else None
            
        elif field_type_str in ["Vector2", "Vector3", "RGBA"]:
            if isinstance(current_value, dict):
                current_str = ", ".join([f"{k}={v}" for k, v in current_value.items()])
            else:
                current_str = ""
            
            text, ok = QInputDialog.getText(
                parent,
                f"Edit {field_name}",
                f"Enter {field_type_str} as comma-separated values (e.g., x=1.0, y=2.0):",
                text=current_str
            )
            
            if not ok:
                return None
                
            # Parse the input
            try:
                result = {}
                parts = text.split(",")
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        key = key.strip()
                        value = float(value.strip())
                        result[key] = value
                return result
            except Exception as e:
                QMessageBox.warning(parent, "Parse Error", f"Could not parse input: {e}")
                return None
                
        elif field_type_str == "EnumString":
            # For enum strings, we would need the enum values list
            # For now, just use text input
            text, ok = QInputDialog.getText(
                parent,
                f"Edit {field_name}",
                f"Enter value for {field_name} (enum):",
                text=str(current_value) if current_value is not None else ""
            )
            return text if ok else None
            
        else:
            # Default to string input for unknown types
            text, ok = QInputDialog.getText(
                parent,
                f"Edit {field_name}",
                f"Enter value for {field_name} ({field_type_str}):",
                text=str(current_value) if current_value is not None else ""
            )
            return text if ok else None