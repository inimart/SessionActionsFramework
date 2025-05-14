# framework_tool/data_models/common_types.py
# All comments and identifiers in English

from enum import Enum

class FieldType(Enum):
    """
    Enumeration of supported field types for SubActionDefinition fields.
    The string values will be used in the JSON output.
    """
    BOOLEAN = "boolean"
    STRING = "string"
    FLOAT = "float"
    INTEGER = "integer"
    VECTOR2 = "Vector2" # For simplicity, we'll store these as dicts in JSON
    VECTOR3 = "Vector3" # e.g., {"x": 0.0, "y": 0.0, "z": 0.0}
    QUATERNION = "Quaternion" # e.g., {"x":0,"y":0,"z":0,"w":1}
    COLOR_RGBA = "ColorRGBA" # e.g., {"r":1,"g":1,"b":1,"a":1}
    ENUM_STRING = "EnumString" # The actual enum values will be stored in SubActionFieldDefinition
    ASSET_PATH_STRING = "AssetPathString" # A string representing a path to a Unity asset
    ITEM_LABEL_REFERENCE = "ItemLabelReference" # A string referencing an ItemLabel

    @classmethod
    def from_string(cls, s: str):
        """Converts a string to a FieldType enum member."""
        for member in cls:
            if member.value == s:
                return member
        raise ValueError(f"'{s}' is not a valid FieldType string.")

    def __str__(self):
        return self.value

# You can add other common enums or simple data structures here if needed later.