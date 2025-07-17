# framework_tool/data_models/action_definition.py
# All comments and identifiers in English

from typing import List, Dict, Any, Optional
from .custom_field_definition import CustomFieldDefinition


class ActionDefinition:
    """
    Defines an Action, identified by an ActionLabel (which will be the key
    in the project's action_definitions dictionary).
    An Action consists of custom fields and behavior configuration.
    """
    def __init__(self,
                 description: str = "",
                 autocomplete: bool = False,
                 custom_fields: Optional[List[CustomFieldDefinition]] = None):
        self.description: str = description
        self.autocomplete: bool = autocomplete
        # Custom fields that can be configured per action instance
        self.custom_fields: List[CustomFieldDefinition] = custom_fields if custom_fields is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "autocomplete": self.autocomplete,
            "customFields": [cf.to_dict() for cf in self.custom_fields]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionDefinition':
        custom_fields_data = data.get("customFields", [])
        custom_fields_list = [CustomFieldDefinition.from_dict(cf_data) for cf_data in custom_fields_data]
        
        return cls(
            description=data.get("description", ""),
            autocomplete=data.get("autocomplete", False),
            custom_fields=custom_fields_list
        )
        
    def get_custom_field_by_name(self, field_name: str) -> Optional[CustomFieldDefinition]:
        """Get a custom field definition by name"""
        for field in self.custom_fields:
            if field.field_name == field_name:
                return field
        return None
        
    def get_default_field_values(self) -> Dict[str, Any]:
        """Get default values for all custom fields"""
        return {field.field_name: field.get_default_value_for_type() for field in self.custom_fields}