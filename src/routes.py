import yaml
import os
import shutil
import logging
import subprocess
import io
import datetime
from flask import Flask, render_template, request, jsonify, send_file
from . import openapi_utils, redocly_cli
from config import TEMP_SPEC_FILE, ROOT_SPEC_FILE

# Get the project root directory (parent of src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_project_path(filename):
    """Returns an absolute path to a file in the project root."""
    return os.path.join(PROJECT_ROOT, filename)

# --- Logging Configuration ---
# Create a 'logs' directory if it doesn't exist at the project root.
log_dir = get_project_path('logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Generate log filename based on the current date (e.g., 081025.log)
log_filename = os.path.join(log_dir, datetime.datetime.now().strftime('%d%m%y.log'))

# This sets up a new log file for each day inside the 'logs' folder.
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO, # Set the minimum level of messages to record
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# --- End Logging Configuration ---

# The template_folder and static_folder paths are relative to this file's location
app = Flask(__name__, template_folder='../templates', static_folder='../static')

def _is_filename_valid(filename, allowed_extensions):
    """
    Validates a filename to ensure it's safe and has a correct extension.
    Prevents path traversal and checks for emptiness.
    """
    if not filename:
        return False
    # Prevent directory traversal attacks
    if '/' in filename or '\\' in filename or '..' in filename:
        return False
    # Ensure the file ends with one of the allowed extensions
    return any(filename.endswith(ext) for ext in allowed_extensions)

@app.route('/')
def index():
    """Serves the main HTML user interface."""
    logging.info("Serving main page.")
    return render_template('index.html')

@app.route('/api/paths', methods=['GET'])
def get_paths_endpoint():
    """Endpoint to get API paths grouped by tag for the Bundler UI."""
    logging.info("Request received for /api/paths")
    try:
        grouped_paths = openapi_utils.get_grouped_paths()
        return jsonify({"groups": grouped_paths})
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}")
        return jsonify({"error": f"Could not load paths from '{ROOT_SPEC_FILE}'. Please ensure the file exists."}), 500
    except Exception as e:
        logging.exception("An unexpected error occurred in get_paths_endpoint")
        return jsonify({"error": "An unexpected error occurred on the server."}), 500

@app.route('/api/bundle', methods=['POST'])
def bundle_spec_endpoint():
    """Endpoint to bundle a spec based on user selections."""
    data = request.json
    output_filename = data.get('filename', 'bundled.yaml')

    # --- Server-Side Filename Validation ---
    if not _is_filename_valid(output_filename, ['.yaml', '.yml']):
        logging.warning(f"Invalid filename provided for bundle: '{output_filename}'")
        return jsonify({"success": False, "message": "Invalid filename. It must end with .yaml or .yml"}), 400
    
    logging.info(f"Starting bundle process for output file: '{output_filename}'")
    
    try:
        root_spec = openapi_utils.load_yaml_file(ROOT_SPEC_FILE)
        if not root_spec:
            raise FileNotFoundError(f"Could not load root spec file '{ROOT_SPEC_FILE}'.")

        selected_keys = data.get('paths', [])
        logging.info(f"Selected paths for bundling: {selected_keys}")
        all_paths = root_spec.get('paths', {})
        selected_paths = {key: all_paths[key] for key in selected_keys if key in all_paths}
        
        all_tags = root_spec.get('tags', [])
        required_tags = openapi_utils.get_tags_for_selected_paths(selected_paths)
        filtered_tags = [tag for tag in all_tags if tag.get('name') in required_tags]
        
        temp_spec = {k: v for k, v in root_spec.items() if k not in ['paths', 'tags']}
        temp_spec.update({'tags': filtered_tags, 'paths': selected_paths})
        
        temp_file_path = get_project_path(TEMP_SPEC_FILE)
        output_file_path = get_project_path(output_filename)
        
        with open(temp_file_path, 'w') as f:
            yaml.dump(temp_spec, f, sort_keys=False)
            
        redocly_cli.bundle_spec(temp_file_path, output_file_path)
        logging.info(f"Bundle '{output_filename}' generated successfully.")
        
        with open(output_file_path, 'rb') as f:
            file_data = f.read()
        
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=output_filename)

    except (subprocess.CalledProcessError, Exception) as e:
        error_message = getattr(e, 'stderr', str(e))
        logging.error(f"Bundling failed: {error_message}")
        return jsonify({"success": False, "message": f"Error: {error_message}"}), 500
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        if os.path.exists(output_file_path): os.remove(output_file_path)

@app.route('/api/split', methods=['POST'])
def split_spec_endpoint():
    """Endpoint to split a monolithic file and update the project."""
    logging.info("Starting split process.")
    temp_input_file = get_project_path("temp_monolith_for_splitting.yaml")
    temp_output_dir = get_project_path("temp_split_output")
    try:
        with open(temp_input_file, 'w') as f:
            f.write(request.data.decode('utf-8'))
        
        if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)
        os.makedirs(temp_output_dir)
        
        redocly_cli.split_spec(temp_input_file, temp_output_dir)
        
        for item in os.listdir(temp_output_dir):
            src_path = os.path.join(temp_output_dir, item)
            dest_path = get_project_path(item)
            if os.path.isdir(src_path):
                if os.path.exists(dest_path): shutil.rmtree(dest_path)
                shutil.move(src_path, dest_path)
            else:
                shutil.move(src_path, dest_path)
        
        logging.info("Project split and updated successfully.")
        return jsonify({"success": True, "message": "Project updated! Please restart the server and refresh this page."})
    except (subprocess.CalledProcessError, Exception) as e:
        error_message = getattr(e, 'stderr', str(e))
        logging.error(f"Splitting failed: {error_message}")
        return jsonify({"success": False, "message": f"Error: {error_message}"}), 500
    finally:
        if os.path.exists(temp_input_file): os.remove(temp_input_file)
        if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)

@app.route('/api/build', methods=['POST'])
def build_docs_endpoint():
    """Receives a bundled YAML and returns a standalone HTML file."""
    data = request.json
    output_filename = data.get('filename', 'api-docs.html')

    # --- Server-Side Filename Validation ---
    if not _is_filename_valid(output_filename, ['.html', '.htm']):
        logging.warning(f"Invalid filename provided for build: '{output_filename}'")
        return jsonify({"success": False, "message": "Invalid filename. It must end with .html or .htm and not contain path characters."}), 400

    logging.info(f"Starting build-docs process for '{output_filename}'")
    
    temp_input_file = get_project_path("temp_bundle_for_build.yaml")
    temp_output_file = get_project_path("temp_docs.html")
    
    try:
        spec_content = data.get('spec_content')
        if not spec_content:
            logging.warning("Build-docs request received with no spec content.")
            return jsonify({"success": False, "message": "No spec content provided."}), 400
            
        with open(temp_input_file, 'w') as f:
            yaml.dump(spec_content, f)
            
        redocly_cli.build_docs(temp_input_file, temp_output_file)
        logging.info("Docs built successfully.")
        
        with open(temp_output_file, 'rb') as f:
            file_data = f.read()

        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=output_filename)

    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed: {e.stderr}")
        return jsonify({"success": False, "message": f"Redocly Build Error: {e.stderr}"}), 500
    except Exception as e:
        logging.exception("An unexpected error occurred in build_docs_endpoint")
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_input_file): os.remove(temp_input_file)
        if os.path.exists(temp_output_file): os.remove(temp_output_file)

