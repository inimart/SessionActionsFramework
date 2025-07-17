# framework_tool/data_models/custom_field_definition.py
# All comments and identifiers in English

from typing import List, Dict, Any, Optional
from .common_types import FieldType


class CustomFieldDefinition:
    """
    Defines a custom field that can be added to an Action.
    Each field has a name, type, and optional configuration (like enum values or default value).
    """
    def __init__(self,
                 field_name: str,
                 field_type: FieldType,
                 default_value: Any = None,
                 enum_values: Optional[List[str]] = None):
        if not field_name:
            raise ValueError("field_name cannot be empty.")

        self.field_name: str = field_name
        self.field_type: FieldType = field_type
        self.default_value: Any = default_value
        # For ENUM_STRING type, this list contains the allowed values
        self.enum_values: List[str] = enum_values if enum_values is not None else []

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "fieldName": self.field_name,
            "fieldType": self.field_type.value,
        }
        if self.default_value is not None:
            data["defaultValue"] = self.default_value
        if self.enum_values:
            data["enumValues"] = self.enum_values
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomFieldDefinition':
        field_name = data.get("fieldName")
        if not field_name:
            raise ValueError("fieldName is required for CustomFieldDefinition.")

        field_type_str = data.get("fieldType")
        if not field_type_str:
            raise ValueError("fieldType is required for CustomFieldDefinition.")

        try:
            field_type = FieldType.from_string(field_type_str)
        except ValueError as e:
            raise ValueError(f"Invalid fieldType '{field_type_str}': {e}")

        return cls(
            field_name=field_name,
            field_type=field_type,
            default_value=data.get("defaultValue"),
            enum_values=data.get("enumValues", [])
        )

    def get_default_value_for_type(self) -> Any:
        """Returns a sensible default value based on the field type"""
        if self.default_value is not None:
            return self.default_value
            
        if self.field_type == FieldType.BOOLEAN:
            return False
        elif self.field_type == FieldType.STRING:
            return ""
        elif self.field_type == FieldType.FLOAT:
            return 0.0
        elif self.field_type == FieldType.INTEGER:
            return 0
        elif self.field_type == FieldType.VECTOR2:
            return {"x": 0.0, "y": 0.0}
        elif self.field_type == FieldType.VECTOR3:
            return {"x": 0.0, "y": 0.0, "z": 0.0}
        elif self.field_type == FieldType.RGBA:
            return {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        elif self.field_type == FieldType.ENUM_STRING:
            return self.enum_values[0] if self.enum_values else ""
        elif self.field_type == FieldType.ITEM_LABEL_REFERENCE:
            return ""  # Will be set from dropdown in UI
        else:
            return None