# framework_tool/data_models/action_definition.py
# All comments and identifiers in English

from typing import List, Dict, Any, Optional

# We don't need to import SubActionDefinition or other classes for type hints
# if we use strings, but for clarity, it's fine if they are simple data classes
# that don't create circular dependencies at the module level.
# For now, we'll assume direct imports are fine as they are just data structures.
# from .sub_action_definition import SubActionDefinition # Not directly needed here

class ConfiguredSubAction:
    """
    Represents a SubAction that has been configured and added to an ActionDefinition.
    It specifies which SubActionDefinition (template) to use, an optional target ItemLabel,
    and the specific values for the properties defined in that SubActionDefinition.
    """
    def __init__(self,
                 sub_action_label_to_use: str, # References a SubActionDefinition's label
                 item_label_for_target: Optional[str] = None,
                 property_values: Optional[Dict[str, Any]] = None):
        
        if not sub_action_label_to_use:
            raise ValueError("sub_action_label_to_use cannot be empty.")

        self.sub_action_label_to_use: str = sub_action_label_to_use
        self.item_label_for_target: Optional[str] = item_label_for_target
        # property_values will store the actual values for fields defined in the
        # corresponding SubActionDefinition.
        # e.g., {"isEnabled": True, "speed": 2.5}
        self.property_values: Dict[str, Any] = property_values if property_values is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "subActionLabelToUse": self.sub_action_label_to_use,
            "propertyValues": self.property_values # Store as is
        }
        if self.item_label_for_target is not None: # Only include if set
            data["itemLabelForTarget"] = self.item_label_for_target
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfiguredSubAction':
        sub_action_label = data.get("subActionLabelToUse")
        if not sub_action_label:
            raise ValueError("subActionLabelToUse is required for ConfiguredSubAction.")
            
        return cls(
            sub_action_label_to_use=sub_action_label,
            item_label_for_target=data.get("itemLabelForTarget"), # Will be None if not present
            property_values=data.get("propertyValues", {})
        )


class ActionDefinition:
    """
    Defines an Action, identified by an ActionLabel (which will be the key
    in the project's action_definitions dictionary).
    An Action consists of an ordered list of configured SubActions.
    """
    def __init__(self,
                 # action_label: str, # The label itself is the key in the parent dict
                 help_label: str = "",
                 description: str = "",
                 sub_actions: Optional[List[ConfiguredSubAction]] = None):
        # self.action_label: str = action_label # Not stored here, used as dict key
        self.help_label: str = help_label
        self.description: str = description
        # The order of sub_actions is important as it defines the sequence
        # in which they are performed to enable/execute the Action.
        self.sub_actions: List[ConfiguredSubAction] = sub_actions if sub_actions is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            # "actionLabel": self.action_label, # Not needed if it's the key
            "helpLabel": self.help_label,
            "description": self.description,
            "subActions": [sa.to_dict() for sa in self.sub_actions] # Preserve order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionDefinition':
        # action_label = data.get("actionLabel") # Not present if it was the key
        # if not action_label:
        #     raise ValueError("actionLabel is required for ActionDefinition.")

        sub_actions_data = data.get("subActions", [])
        sub_actions_list = [ConfiguredSubAction.from_dict(sa_data) for sa_data in sub_actions_data]
        
        return cls(
            # action_label=action_label,
            help_label=data.get("helpLabel", ""),
            description=data.get("description", ""),
            sub_actions=sub_actions_list
        )