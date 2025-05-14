# create_project_structure.py
# Script to create the directory structure and empty Python files for the framework tool.
# All comments and identifiers in English.

import os

# --- Configuration ---
# Define the name of the root directory for your project
ROOT_PROJECT_DIR = "." # This will be created if it doesn't exist

# Define the structure. Tuples are (path_relative_to_root, is_directory)
# Files will be created empty with UTF-8 encoding.
PROJECT_STRUCTURE = [
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool"), True),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "__init__.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models"), True),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "__init__.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "common_types.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "project_data.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "sub_action_definition.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "action_definition.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "data_models", "session_graph.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "project_io"), True),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "project_io", "__init__.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "project_io", "json_handler.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui"), True),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui", "__init__.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui", "main_window.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui", "widgets"), True),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui", "widgets", "__init__.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "gui", "widgets", "label_editor_widget.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "framework_tool", "main.py"), False),
    (os.path.join(ROOT_PROJECT_DIR, "README.md"), False), # Will create an empty README
    (os.path.join(ROOT_PROJECT_DIR, "requirements.txt"), False), # Empty requirements file
    (os.path.join(ROOT_PROJECT_DIR, "test_data_models.py"), False), # Empty test script placeholder
    (os.path.join(ROOT_PROJECT_DIR, "convert_encoding.py"), False), # Empty encoding script placeholder
]

def create_structure():
    """Creates the directories and empty UTF-8 encoded files."""
    print(f"Creating project structure under '{os.path.abspath(ROOT_PROJECT_DIR)}'...")

    for path_str, is_dir in PROJECT_STRUCTURE:
        # Ensure the path uses the correct OS separator
        path_os_specific = os.path.normpath(path_str)
        
        try:
            if is_dir:
                os.makedirs(path_os_specific, exist_ok=True)
                print(f"Ensured directory exists: {path_os_specific}")
            else:
                # Ensure parent directory exists before creating file
                parent_dir = os.path.dirname(path_os_specific)
                if parent_dir: # Check if parent_dir is not empty (e.g. for files in root)
                    os.makedirs(parent_dir, exist_ok=True)
                
                # Create an empty file with UTF-8 encoding (without BOM)
                with open(path_os_specific, 'w', encoding='utf-8') as f:
                    # For .py files, you might want a basic comment
                    if path_os_specific.endswith(".py"):
                        f.write(f"# {os.path.basename(path_os_specific)}\n")
                        f.write("# All comments and identifiers in English\n\n")
                    # For other files, just creating them empty is fine.
                    pass 
                print(f"Created empty file (UTF-8): {path_os_specific}")
        except OSError as e:
            print(f"Error creating {path_os_specific}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with {path_os_specific}: {e}")

    print("\nProject structure creation complete.")
    print(f"Next steps:")
    print(f"1. Navigate to '{os.path.abspath(ROOT_PROJECT_DIR)}'.")
    print(f"2. Create and activate a new virtual environment in the '{os.path.join(ROOT_PROJECT_DIR, 'venv')}' directory (or delete and recreate if it exists from a bad state).")
    print(f"   Example: python -m venv {os.path.join(ROOT_PROJECT_DIR, 'venv')}")
    print(f"            {os.path.join(ROOT_PROJECT_DIR, 'venv', 'Scripts', 'activate')} (Windows)")
    print(f"            source {os.path.join(ROOT_PROJECT_DIR, 'venv', 'bin', 'activate')} (macOS/Linux)")
    print(f"3. Install necessary packages into the new venv: pip install --upgrade pip setuptools wheel PySide6 networkx chardet")
    print(f"4. You can then start populating the created .py files with the code we've discussed.")

if __name__ == "__main__":
    # --- Safety Check ---
    target_setup_directory = os.path.abspath(ROOT_PROJECT_DIR)
    
    # Check if the root project directory already exists
    if os.path.exists(target_setup_directory) and os.listdir(target_setup_directory):
        # Directory exists and is not empty
        confirm = input(
            f"The directory '{target_setup_directory}' already exists and is not empty.\n"
            f"This script will create missing files/folders and overwrite empty files if they match the structure.\n"
            f"It will NOT delete existing non-empty files or other unexpected files/folders.\n"
            f"Do you want to proceed? (yes/no): "
        )
        if confirm.lower() != 'yes':
            print("Operation cancelled by the user.")
            exit()
    elif not os.path.exists(target_setup_directory):
         confirm_create = input(
            f"The directory '{target_setup_directory}' does not exist and will be created.\n"
            f"Do you want to proceed? (yes/no): "
        )
         if confirm_create.lower() != 'yes':
            print("Operation cancelled by the user.")
            exit()

    create_structure()