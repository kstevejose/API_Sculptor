import yaml
from config import ROOT_SPEC_FILE

def load_yaml_file(filename):
    """Safely loads and parses a YAML file."""
    try:
        with open(filename, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        print(f"Warning: Could not load or parse {filename}")
        return None

def get_tags_for_selected_paths(selected_paths):
    """Finds all unique tags used by the selected paths by reading their referenced files."""
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
    """Scans the OpenAPI paths, groups them by tag, and returns a structured dictionary."""
    root_spec = load_yaml_file(ROOT_SPEC_FILE)
    if not (root_spec and 'paths' in root_spec):
        raise FileNotFoundError(f"Could not load paths from '{ROOT_SPEC_FILE}'")
    
    grouped_paths = {}
    for path_string, path_data in root_spec.get('paths', {}).items():
        if '$ref' not in path_data:
            continue
        path_content = load_yaml_file(path_data['$ref'])
        if not path_content:
            continue
        
        for _, details in path_content.items():
            if not isinstance(details, dict):
                continue
            
            summary = details.get('summary', 'No summary available.')
            tags = details.get('tags', ['Untagged'])
            main_tag = tags[0]

            if main_tag not in grouped_paths:
                grouped_paths[main_tag] = []
            
            grouped_paths[main_tag].append({"path": path_string, "summary": summary})
            break  # Process only the first HTTP method for path info
            
    return grouped_paths
