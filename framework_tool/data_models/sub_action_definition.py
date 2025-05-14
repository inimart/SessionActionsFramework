# framework_tool/data_models/sub_action_definition.py
# All comments and identifiers in English

from typing import List, Dict, Any, Optional, Union

from .common_types import FieldType # Import FieldType from common_types.py

class SubActionFieldDefinition:
    """
    Defines a single customizable field within a SubActionDefinition.
    For example, a 'PlayAnimation' SubActionDefinition might have fields for 'animationName' (string)
    and 'speed' (float).
    """
    def __init__(self,
                 field_name: str,
                 field_type: FieldType,
                 default_value: Optional[Any] = None, # Must match field_type
                 enum_values: Optional[List[str]] = None): # Only relevant if field_type is FieldType.ENUM_STRING
        
        if not field_name:
            raise ValueError("Field name cannot be empty.")
        if not isinstance(field_type, FieldType):
            raise ValueError("field_type must be an instance of FieldType enum.")

        self.field_name: str = field_name
        self.field_type: FieldType = field_type
        self.default_value: Optional[Any] = default_value
        
        if self.field_type == FieldType.ENUM_STRING:
            if not enum_values: # or not isinstance(enum_values, list) or not all(isinstance(e, str) for e in enum_values):
                raise ValueError("enum_values must be a non-empty list of strings for EnumString FieldType.")
            self.enum_values: Optional[List[str]] = sorted(list(set(enum_values))) # Store unique, sorted values
        elif enum_values is not None:
            # If field_type is not ENUM_STRING, enum_values should not be provided.
            # We could raise a warning or error, or just ignore it. For now, let's ignore.
            self.enum_values = None
        else:
            self.enum_values = None

        # Future: Add validation for default_value against field_type if needed.

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "fieldName": self.field_name,
            "fieldType": self.field_type.value # Store the string value of the enum
        }
        if self.default_value is not None:
            data["defaultValue"] = self.default_value
        if self.field_type == FieldType.ENUM_STRING and self.enum_values:
            data["enumValues"] = self.enum_values
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubActionFieldDefinition':
        field_name = data.get("fieldName")
        field_type_str = data.get("fieldType")
        
        if not field_name or not field_type_str:
            raise ValueError("fieldName and fieldType are required in SubActionFieldDefinition data.")

        try:
            field_type_enum = FieldType.from_string(field_type_str)
        except ValueError as e:
            raise ValueError(f"Invalid fieldType string '{field_type_str}': {e}")

        return cls(
            field_name=field_name,
            field_type=field_type_enum,
            default_value=data.get("defaultValue"), # Type validation against field_type could be added here
            enum_values=data.get("enumValues")
        )


class SubActionDefinition:
    """
    Defines the template for a type of SubAction.
    It's identified by a SubActionLabel (which will be the key in the project's
    sub_action_definitions dictionary).
    """
    def __init__(self,
                 # sub_action_label: str, # The label itself is the key in the parent dict
                 description: str = "",
                 needs_target_item: bool = False,
                 fields: Optional[List[SubActionFieldDefinition]] = None):
        # self.sub_action_label: str = sub_action_label # Not stored here, used as dict key
        self.description: str = description
        self.needs_target_item: bool = needs_target_item
        self.fields: List[SubActionFieldDefinition] = fields if fields is not None else []
        
        # Ensure field names are unique within this definition
        if fields:
            field_names = [f.field_name for f in fields]
            if len(field_names) != len(set(field_names)):
                raise ValueError("Field names within a SubActionDefinition must be unique.")


    def to_dict(self) -> Dict[str, Any]:
        return {
            # "subActionLabel": self.sub_action_label, # Not needed if it's the key
            "description": self.description,
            "needsTargetItem": self.needs_target_item,
            "fields": sorted([field.to_dict() for field in self.fields], key=lambda f: f["fieldName"]) # Sort for consistent output
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubActionDefinition':
        # sub_action_label = data.get("subActionLabel") # Not present if it was the key
        # if not sub_action_label:
        #     raise ValueError("subActionLabel is required for SubActionDefinition.")
            
        fields_data = data.get("fields", [])
        fields_list = [SubActionFieldDefinition.from_dict(fd) for fd in fields_data]

        return cls(
            # sub_action_label=sub_action_label,
            description=data.get("description", ""),
            needs_target_item=data.get("needsTargetItem", False),
            fields=fields_list
        )