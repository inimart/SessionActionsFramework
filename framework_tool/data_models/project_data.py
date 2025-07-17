# framework_tool/data_models/project_data.py
# All comments and identifiers in English

import datetime
import uuid
from typing import List, Dict, Any

# Forward declarations for type hinting to avoid circular imports
# These will be actual classes defined in other files.
if False: # TYPE_CHECKING block for linters/type checkers
    from .sub_action_definition import SubActionDefinition
    from .action_definition import ActionDefinition
    from .session_graph import SessionActionsGraph


class ProjectMetadata:
    """
    Contains metadata for the project.
    """
    def __init__(self,
                 project_name: str = "New SessionActions Project",
                 format_version: str = "1.0.0",
                 creation_date: str = None, # ISO 8601 timestamp string
                 author: str = ""):
        self.project_name: str = project_name
        self.format_version: str = format_version
        self.creation_date: str = creation_date if creation_date else datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.author: str = author

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectName": self.project_name,
            "formatVersion": self.format_version,
            "creationDate": self.creation_date,
            "author": self.author
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        return cls(
            project_name=data.get("projectName", "New Project"),
            format_version=data.get("formatVersion", "1.0.0"),
            creation_date=data.get("creationDate"), # Will be auto-generated if None
            author=data.get("author", "")
        )


class ProjectData:
    """
    Root class for storing all data related to a project.
    This class will be serialized to/from the main project JSON file.
    """
    def __init__(self):
        self.project_metadata: ProjectMetadata = ProjectMetadata()
        self.action_labels: List[str] = []
        self.item_labels: List[str] = []
        self.sub_action_labels: List[str] = []
        
        # Type hints using strings to avoid immediate import, actual types are SubActionDefinition, ActionDefinition, SessionActionsGraph
        self.sub_action_definitions: Dict[str, 'SubActionDefinition'] = {} # Key: SubActionLabel (str)
        self.action_definitions: Dict[str, 'ActionDefinition'] = {}       # Key: ActionLabel (str)
        self.session_actions: List['SessionActionsGraph'] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectMetadata": self.project_metadata.to_dict(),
            "actionLabels": sorted(list(set(self.action_labels))), # Ensure uniqueness and order
            "itemLabels": sorted(list(set(self.item_labels))),
            "subActionLabels": sorted(list(set(self.sub_action_labels))),
            "subActionDefinitions": {
                key: definition.to_dict()
                for key, definition in sorted(self.sub_action_definitions.items()) # Sort by key for consistent output
            },
            "actionDefinitions": {
                key: definition.to_dict()
                for key, definition in sorted(self.action_definitions.items())
            },
            "sessionActions": [
                graph.to_dict()
                for graph in sorted(self.session_actions, key=lambda g: g.session_name) # Sort by name
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any],
                  # Pass class types for deserialization to avoid direct imports here
                  action_def_cls,
                  session_graph_cls) -> 'ProjectData':
        instance = cls()
        instance.project_metadata = ProjectMetadata.from_dict(data.get("projectMetadata", {}))
        instance.action_labels = data.get("actionLabels", [])
        instance.item_labels = data.get("itemLabels", [])
        # SubAction references removed - backwards compatibility with old files
        instance.sub_action_labels = data.get("subActionLabels", [])  # Keep for loading old files
        instance.sub_action_definitions = data.get("subActionDefinitions", {})  # Keep for loading old files

        instance.action_definitions = {
            key: action_def_cls.from_dict(definition_data)
            for key, definition_data in data.get("actionDefinitions", {}).items()
        }
        instance.session_actions = [
            session_graph_cls.from_dict(graph_data)
            for graph_data in data.get("sessionActions", [])
        ]
        return instance