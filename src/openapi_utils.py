import yaml
import os
from config import ROOT_SPEC_FILE

# Get the project root directory (parent of src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_project_path(filename):
    """Returns an absolute path to a file in the project root."""
    return os.path.join(PROJECT_ROOT, filename)

def load_yaml_file(filename):
    """Loads and parses any given YAML file."""
    try:
        # Always use project root path
        filepath = get_project_path(filename)
        
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        # Return None on failure to be handled by the caller
        return None

def get_tags_for_selected_paths(selected_paths):
    """Finds all unique tags used by the selected paths by reading their files."""
    collected_tag_names = set()
    for path_data in selected_paths.values():
        if '$ref' in path_data:
            path_file = path_data['$ref']
            path_content = load_yaml_file(path_file)
            if not path_content:
                continue
            for method_details in path_content.values():
                if isinstance(method_details, dict) and 'tags' in method_details:
                    collected_tag_names.update(method_details['tags'])
    return collected_tag_names

def get_grouped_paths():
    """
    Scans the OpenAPI paths from the ROOT_SPEC_FILE, groups them by tag,
    and returns a structured dictionary for the UI.
    """
    root_spec = load_yaml_file(ROOT_SPEC_FILE)
    if not (root_spec and 'paths' in root_spec):
        raise FileNotFoundError(f"Root spec file '{ROOT_SPEC_FILE}' not found or is invalid.")

    grouped_paths = {}
    for path_string, path_data in root_spec.get('paths', {}).items():
        if '$ref' not in path_data:
            continue

        path_content = load_yaml_file(path_data['$ref'])
        if not path_content:
            continue
        
        for method, details in path_content.items():
            if not isinstance(details, dict):
                continue

            summary = details.get('summary', 'No summary available.')
            
            tags = details.get('tags', ['Untagged'])
            main_tag = tags[0]

            if main_tag not in grouped_paths:
                grouped_paths[main_tag] = []
            
            grouped_paths[main_tag].append({
                "path": path_string,
                "summary": summary
            })
            break 
            
    return grouped_paths