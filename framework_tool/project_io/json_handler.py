# framework_tool/project_io/json_handler.py
# All comments and identifiers in English

import json
import os
from typing import Dict, Any

# Import data model classes from the data_models package
# We need to import them to pass their .from_dict class methods
from ..data_models.project_data import ProjectData
from ..data_models.sub_action_definition import SubActionDefinition
from ..data_models.action_definition import ActionDefinition
from ..data_models.session_graph import SessionActionsGraph

# Define the current version of the JSON format this handler supports.
# This should match ProjectMetadata.format_version for new projects.
SUPPORTED_FORMAT_VERSION = "1.0.0"

def new_project(project_name: str = "New SessionActions Project", author: str = "") -> ProjectData:
    """
    Creates a new, empty ProjectData object with default metadata.
    """
    project = ProjectData()
    project.project_metadata.project_name = project_name
    project.project_metadata.author = author
    project.project_metadata.format_version = SUPPORTED_FORMAT_VERSION 
    # creation_date is handled by ProjectMetadata constructor
    return project

def save_project(project_data: ProjectData, filepath: str) -> None:
    """
    Serializes the ProjectData object to JSON and saves it to the specified filepath.
    Args:
        project_data: The ProjectData object to save.
        filepath: The path to the file where the JSON data will be saved.
    Raises:
        IOError: If there's an error writing the file.
        TypeError: If the project_data is not a ProjectData instance.
        Exception: For other potential errors during serialization.
    """
    if not isinstance(project_data, ProjectData):
        raise TypeError("project_data must be an instance of ProjectData.")

    try:
        # Ensure the format version is current upon saving
        project_data.project_metadata.format_version = SUPPORTED_FORMAT_VERSION
        
        data_dict = project_data.to_dict()
        
        # Create directory if it doesn't exist
        dir_name = os.path.dirname(filepath)
        if dir_name: # Ensure dir_name is not empty (e.g. if filepath is just a filename)
            os.makedirs(dir_name, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2) # indent for readability
        print(f"Project saved successfully to {filepath}")

    except IOError as e:
        print(f"Error saving project to {filepath}: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while saving project: {e}")
        raise


def load_project(filepath: str) -> ProjectData:
    """
    Loads project data from a JSON file and deserializes it into a ProjectData object.
    Args:
        filepath: The path to the JSON file to load.
    Returns:
        A ProjectData object populated with the data from the file.
    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an error reading the file.
        json.JSONDecodeError: If the file content is not valid JSON.
        ValueError: If the JSON data is missing required fields or has an unsupported format version.
        Exception: For other potential errors during deserialization.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)

        # Basic validation: check format version if present
        format_version = data_dict.get("projectMetadata", {}).get("formatVersion")
        if format_version and format_version != SUPPORTED_FORMAT_VERSION:
            # For now, we're strict. Later, we might add logic for migrating older versions.
            print(f"Warning: Project file format version '{format_version}' is different from "
                  f"supported version '{SUPPORTED_FORMAT_VERSION}'. Attempting to load anyway.")
            # raise ValueError(f"Unsupported project format version: {format_version}. "
            #                  f"Expected: {SUPPORTED_FORMAT_VERSION}")

        # Pass the class constructors to the ProjectData.from_dict method
        # to handle the creation of nested objects correctly.
        project_data = ProjectData.from_dict(
            data_dict,
            sub_action_def_cls=SubActionDefinition,
            action_def_cls=ActionDefinition,
            session_graph_cls=SessionActionsGraph
        )
        
        # Ensure the loaded project has the supported format version after loading
        # (in case it was missing or we are migrating)
        if project_data.project_metadata.format_version != SUPPORTED_FORMAT_VERSION:
             print(f"Note: Project metadata format version updated to '{SUPPORTED_FORMAT_VERSION}' upon loading.")
             project_data.project_metadata.format_version = SUPPORTED_FORMAT_VERSION
        
        print(f"Project loaded successfully from {filepath}")
        return project_data

    except FileNotFoundError:
        print(f"Error: Project file not found at {filepath}")
        raise
    except IOError as e:
        print(f"Error loading project from {filepath}: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        raise
    except ValueError as e: # Catches ValueErrors from from_dict methods
        print(f"Error validating data from {filepath}: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while loading project: {e}")
        raise