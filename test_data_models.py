# hygiene_vr_framework/test_data_models.py
# All comments and identifiers in English

import os
import shutil # For cleaning up test files/dirs
import uuid 
# Adjust the Python path to import from the framework_tool package
# This is a common way to do it for scripts outside a package
# that need to import from the package.
import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # If test_data_models.py was in a subfolder
# Since test_data_models.py is in the root alongside framework_tool,
# Python should be able to find framework_tool if you run the script from the root.
# If not, you might need to set PYTHONPATH or use the above sys.path manipulation.

from framework_tool.data_models.common_types import FieldType
from framework_tool.data_models.project_data import ProjectData, ProjectMetadata
from framework_tool.data_models.sub_action_definition import SubActionFieldDefinition, SubActionDefinition
from framework_tool.data_models.action_definition import ConfiguredSubAction, ActionDefinition
from framework_tool.data_models.session_graph import ActionNode, SessionActionsGraph
from framework_tool.project_io import json_handler # Imports functions like new_project, save_project, load_project

# --- Test Configuration ---
TEST_OUTPUT_DIR = "test_output"
TEST_PROJECT_FILENAME = "test_project_data.json"
TEST_PROJECT_FILEPATH = os.path.join(TEST_OUTPUT_DIR, TEST_PROJECT_FILENAME)

def create_sample_project_data() -> ProjectData:
    """Creates a ProjectData object populated with sample data for testing."""
    
    print("Creating sample project data...")
    project = json_handler.new_project(project_name="Hygiene VR Test Suite", author="Test Script")

    # 1. Populate Labels
    project.action_labels = ["WashHands", "DryHands", "OpenDoor", "WearGloves"]
    project.item_labels = ["SoapDispenser", "WaterTap", "PaperTowel", "DoorHandle", "GlovesBox"]
    project.sub_action_labels = ["ActivateGameObject", "PlayAnimation", "CheckPlayerProximity", "ModifyMaterial"]

    # 2. Populate SubActionDefinitions
    # Example: ActivateGameObject
    activate_field = SubActionFieldDefinition(field_name="isActive", field_type=FieldType.BOOLEAN, default_value=True)
    activate_def = SubActionDefinition(
        description="Activates or deactivates a GameObject.",
        needs_target_item=True,
        fields=[activate_field]
    )
    project.sub_action_definitions["ActivateGameObject"] = activate_def

    # Example: PlayAnimation
    anim_name_field = SubActionFieldDefinition(field_name="animationName", field_type=FieldType.STRING)
    anim_speed_field = SubActionFieldDefinition(field_name="speed", field_type=FieldType.FLOAT, default_value=1.0)
    anim_wait_field = SubActionFieldDefinition(field_name="waitForCompletion", field_type=FieldType.BOOLEAN, default_value=False)
    play_anim_def = SubActionDefinition(
        description="Plays an animation on a target.",
        needs_target_item=True,
        fields=[anim_name_field, anim_speed_field, anim_wait_field]
    )
    project.sub_action_definitions["PlayAnimation"] = play_anim_def
    
    # Example: Vector3 SubAction
    move_to_pos_target_field = SubActionFieldDefinition(field_name="targetPosition", field_type=FieldType.VECTOR3)
    move_to_pos_duration_field = SubActionFieldDefinition(field_name="duration", field_type=FieldType.FLOAT, default_value=0.0)
    move_to_pos_def = SubActionDefinition(
        description="Moves an object to a position.",
        needs_target_item=True,
        fields=[move_to_pos_target_field, move_to_pos_duration_field]
    )
    project.sub_action_definitions["MoveToPosition"] = move_to_pos_def


    # 3. Populate ActionDefinitions
    # Example: OpenDoor
    open_door_anim_sub = ConfiguredSubAction(
        sub_action_label_to_use="PlayAnimation",
        item_label_for_target="DoorHandle",
        property_values={"animationName": "Door_Open_Anim", "speed": 1.0, "waitForCompletion": True}
    )
    open_door_activate_sub = ConfiguredSubAction(
        sub_action_label_to_use="ActivateGameObject",
        item_label_for_target="DoorHandle", # Assuming door handle interaction enables/disables something
        property_values={"isActive": False} # e.g., disable collider after opening
    )
    open_door_action_def = ActionDefinition(
        help_label="Open the specified door.",
        description="Activates the door opening sequence, plays animation, and handles interaction state.",
        sub_actions=[open_door_anim_sub, open_door_activate_sub]
    )
    project.action_definitions["OpenDoor"] = open_door_action_def
    
    # Example: WashHands
    wash_hands_activate_tap_sub = ConfiguredSubAction(
        sub_action_label_to_use="ActivateGameObject",
        item_label_for_target="WaterTap",
        property_values={"isActive": True}
    )
    wash_hands_move_sub = ConfiguredSubAction(
        sub_action_label_to_use="MoveToPosition",
        item_label_for_target="SoapDispenser", # Example, maybe player moves hands to dispenser
        property_values={"targetPosition": {"x":1.0, "y":0.5, "z":0.2}, "duration":1.0}
    )
    wash_hands_action_def = ActionDefinition(
        help_label="Wash hands procedure.",
        description="Activates tap and simulates hand washing steps.",
        sub_actions=[wash_hands_activate_tap_sub, wash_hands_move_sub]
    )
    project.action_definitions["WashHands"] = wash_hands_action_def


    # 4. Populate a simple SessionActionsGraph
    node1_id = str(uuid.uuid4()) # Ensure we have IDs for linking
    node2_id = str(uuid.uuid4())
    node3_id = str(uuid.uuid4())

    node1 = ActionNode(node_id=node1_id, action_label_to_execute="OpenDoor", children_node_ids=[node2_id])
    node2 = ActionNode(node_id=node2_id, action_label_to_execute="WashHands", parent_node_id=node1_id, children_node_ids=[node3_id])
    # Node 3 is a child of Node 2, but uses same ActionLabel as Node 1 for testing "ratio interna" if we had parallel nodes
    node3 = ActionNode(node_id=node3_id, action_label_to_execute="OpenDoor", parent_node_id=node2_id)


    session_graph = SessionActionsGraph(
        session_name="BasicHygieneRoutine",
        entry_node_ids=[node1_id],
        nodes=[node1, node2, node3]
    )
    project.session_actions.append(session_graph)

    print("Sample project data created.")
    return project

def verify_project_data(original_project: ProjectData, loaded_project: ProjectData):
    """
    Performs some basic checks to verify that the loaded project data
    matches the original data.
    """
    print("Verifying loaded project data...")
    
    # Metadata
    assert original_project.project_metadata.project_name == loaded_project.project_metadata.project_name
    assert original_project.project_metadata.author == loaded_project.project_metadata.author
    # Format version will be updated to SUPPORTED_FORMAT_VERSION by load_project if it was different or missing
    assert loaded_project.project_metadata.format_version == json_handler.SUPPORTED_FORMAT_VERSION
    print("- Metadata basic check: OK")

    # Labels (checking counts and one example for brevity, to_dict sorts them)
    assert sorted(original_project.action_labels) == sorted(loaded_project.action_labels)
    assert sorted(original_project.item_labels) == sorted(loaded_project.item_labels)
    assert sorted(original_project.sub_action_labels) == sorted(loaded_project.sub_action_labels)
    if original_project.action_labels:
        assert original_project.action_labels[0] in loaded_project.action_labels
    print("- Labels check: OK")

    # SubActionDefinitions (check count and one definition)
    assert len(original_project.sub_action_definitions) == len(loaded_project.sub_action_definitions)
    if "PlayAnimation" in original_project.sub_action_definitions:
        original_sad = original_project.sub_action_definitions["PlayAnimation"]
        loaded_sad = loaded_project.sub_action_definitions.get("PlayAnimation")
        assert loaded_sad is not None
        assert original_sad.description == loaded_sad.description
        assert original_sad.needs_target_item == loaded_sad.needs_target_item
        assert len(original_sad.fields) == len(loaded_sad.fields)
        if original_sad.fields:
            assert original_sad.fields[0].field_name == loaded_sad.fields[0].field_name
            assert original_sad.fields[0].field_type == loaded_sad.fields[0].field_type
    print("- SubActionDefinitions check: OK")

    # ActionDefinitions (check count and one definition)
    assert len(original_project.action_definitions) == len(loaded_project.action_definitions)
    if "OpenDoor" in original_project.action_definitions:
        original_ad = original_project.action_definitions["OpenDoor"]
        loaded_ad = loaded_project.action_definitions.get("OpenDoor")
        assert loaded_ad is not None
        assert original_ad.help_label == loaded_ad.help_label
        assert len(original_ad.sub_actions) == len(loaded_ad.sub_actions)
        if original_ad.sub_actions:
            assert original_ad.sub_actions[0].sub_action_label_to_use == loaded_ad.sub_actions[0].sub_action_label_to_use
            assert original_ad.sub_actions[0].property_values == loaded_ad.sub_actions[0].property_values
    print("- ActionDefinitions check: OK")
    
    # SessionActions (check count and one graph)
    assert len(original_project.session_actions) == len(loaded_project.session_actions)
    if original_project.session_actions:
        original_sg = original_project.session_actions[0]
        loaded_sg = loaded_project.session_actions[0] # Assumes only one for this test
        assert original_sg.session_name == loaded_sg.session_name
        assert sorted(original_sg.entry_node_ids) == sorted(loaded_sg.entry_node_ids)
        assert len(original_sg.nodes) == len(loaded_sg.nodes)
        if original_sg.nodes:
            # Find a specific node by ID for more precise comparison if necessary
            original_node_example = original_sg.get_node_by_id(original_sg.nodes[0].node_id)
            loaded_node_example = loaded_sg.get_node_by_id(original_sg.nodes[0].node_id) # Use original ID for lookup
            assert loaded_node_example is not None
            assert original_node_example.action_label_to_execute == loaded_node_example.action_label_to_execute
            assert sorted(original_node_example.children_node_ids) == sorted(loaded_node_example.children_node_ids)
    print("- SessionActions check: OK")

    print("Verification complete. All checks passed (if no assertion errors).")


def main_test():
    """Main function to run the test."""
    
    # Create test output directory if it doesn't exist
    if not os.path.exists(TEST_OUTPUT_DIR):
        os.makedirs(TEST_OUTPUT_DIR)
        print(f"Created test output directory: {TEST_OUTPUT_DIR}")

    # 1. Create sample data
    original_project = create_sample_project_data()

    # 2. Save the project to JSON
    try:
        print(f"Attempting to save project to: {TEST_PROJECT_FILEPATH}")
        json_handler.save_project(original_project, TEST_PROJECT_FILEPATH)
        print(f"Project saved. Please inspect the JSON file: {TEST_PROJECT_FILEPATH}")
    except Exception as e:
        print(f"Error during save_project: {e}")
        return # Stop test if saving fails

    # 3. Load the project from JSON
    try:
        print(f"Attempting to load project from: {TEST_PROJECT_FILEPATH}")
        loaded_project = json_handler.load_project(TEST_PROJECT_FILEPATH)
    except Exception as e:
        print(f"Error during load_project: {e}")
        return # Stop test if loading fails

    # 4. Verify the loaded data
    try:
        verify_project_data(original_project, loaded_project)
    except AssertionError as e:
        print(f"Verification FAILED: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during verification: {e}")
        
    # Optional: Clean up test file after run
    # print(f"Test finished. You can delete the test file: {TEST_PROJECT_FILEPATH}")
    # print(f"And the directory: {TEST_OUTPUT_DIR}")
    # To automatically clean up:
    # if os.path.exists(TEST_PROJECT_FILEPATH):
    #     os.remove(TEST_PROJECT_FILEPATH)
    # if os.path.exists(TEST_OUTPUT_DIR) and not os.listdir(TEST_OUTPUT_DIR): # Remove dir if empty
    #      os.rmdir(TEST_OUTPUT_DIR)
    # elif os.path.exists(TEST_OUTPUT_DIR) and os.listdir(TEST_OUTPUT_DIR) == [TEST_PROJECT_FILENAME]: # Or if only the file was in it
    #      shutil.rmtree(TEST_OUTPUT_DIR)


if __name__ == "__main__":
    # This allows running the test script directly.
    # Ensure your terminal is in the 'hygiene_vr_framework' root directory
    # when you run 'python test_data_models.py'
    # so that 'from framework_tool...' imports work.
    # If you have issues with imports, you might need to:
    # 1. Ensure 'framework_tool' is in PYTHONPATH.
    # 2. Or run as a module: python -m test_data_models (if test_data_models was a module, but it's a script here)
    # The most straightforward way is to run from the root directory.
    
    # For the import `from framework_tool...` to work when running this script directly
    # from the root directory `hygiene_vr_framework`, the `framework_tool` directory
    # needs to be recognized as a package. The presence of `framework_tool/__init__.py`
    # (even if empty) should be sufficient if Python's current working directory is
    # `hygiene_vr_framework`.
    
    # If you still face import issues, try adding the project root to sys.path explicitly:
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = current_dir # Since this script is in the root
    # if project_root not in sys.path:
    #    sys.path.insert(0, project_root)
    # Now the imports should work:
    # from framework_tool.data_models.common_types import FieldType
    # ... etc.

    main_test()