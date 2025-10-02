import yaml
import os
import shutil
import subprocess
import io
from flask import Flask, render_template, request, jsonify, send_file
from . import openapi_utils, redocly_cli
from config import TEMP_SPEC_FILE

# The template_folder path is now relative to this file's location in src/
app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    """Serves the main HTML user interface."""
    return render_template('index.html')

@app.route('/api/paths', methods=['GET'])
def get_paths_endpoint():
    """Endpoint to get API paths grouped by tag for the Bundler UI."""
    try:
        grouped_paths = openapi_utils.get_grouped_paths()
        return jsonify({"groups": grouped_paths})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/api/bundle', methods=['POST'])
def bundle_spec_endpoint():
    """Endpoint to bundle a spec based on user selections."""
    data = request.json
    output_filename = data.get('filename', 'bundled.yaml')
    
    try:
        root_spec = openapi_utils.load_yaml_file('openapi.yaml')
        if not root_spec:
            raise FileNotFoundError("Could not load root spec file 'openapi.yaml'.")

        selected_keys = data.get('paths', [])
        all_paths = root_spec.get('paths', {})
        selected_paths = {key: all_paths[key] for key in selected_keys if key in all_paths}
        
        all_tags = root_spec.get('tags', [])
        required_tags = openapi_utils.get_tags_for_selected_paths(selected_paths)
        filtered_tags = [tag for tag in all_tags if tag.get('name') in required_tags]
        
        temp_spec = {k: v for k, v in root_spec.items() if k not in ['paths', 'tags']}
        temp_spec.update({'tags': filtered_tags, 'paths': selected_paths})
        
        with open(TEMP_SPEC_FILE, 'w') as f:
            yaml.dump(temp_spec, f, sort_keys=False)
            
        redocly_cli.bundle_spec(TEMP_SPEC_FILE, output_filename)
        
        # Read file into memory and delete before sending to avoid Windows file-in-use error
        with open(output_filename, 'rb') as f:
            data = f.read()
        if os.path.exists(output_filename): 
            os.remove(output_filename)
        
        return send_file(io.BytesIO(data), as_attachment=True, download_name=output_filename)

    except (subprocess.CalledProcessError, Exception) as e:
        error_message = getattr(e, 'stderr', str(e))
        return jsonify({"success": False, "message": f"Error: {error_message}"}), 500
    finally:
        if os.path.exists(TEMP_SPEC_FILE): os.remove(TEMP_SPEC_FILE)

@app.route('/api/split', methods=['POST'])
def split_spec_endpoint():
    """Endpoint to split a monolithic file and update the project."""
    temp_input_file = "temp_monolith_for_splitting.yaml"
    temp_output_dir = "temp_split_output"
    try:
        with open(temp_input_file, 'w') as f:
            f.write(request.data.decode('utf-8'))
        
        if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)
        os.makedirs(temp_output_dir)
        
        redocly_cli.split_spec(temp_input_file, temp_output_dir)
        
        # Move the newly split files into the project's root directory
        for item in os.listdir(temp_output_dir):
            src_path = os.path.join(temp_output_dir, item)
            dest_path = os.path.join('.', item)
            if os.path.isdir(src_path):
                if os.path.exists(dest_path): shutil.rmtree(dest_path)
                shutil.move(src_path, dest_path)
            else:
                shutil.move(src_path, dest_path)
                
        return jsonify({"success": True, "message": "Project updated! Please restart the server and refresh this page."})
    except (subprocess.CalledProcessError, Exception) as e:
        error_message = getattr(e, 'stderr', str(e))
        return jsonify({"success": False, "message": f"Error: {error_message}"}), 500
    finally:
        if os.path.exists(temp_input_file): os.remove(temp_input_file)
        if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)

@app.route('/api/diff', methods=['POST'])
def diff_specs_endpoint():
    """Endpoint to compare two OpenAPI specification files."""
    old_file_path = "temp_diff_old.yaml"
    new_file_path = "temp_diff_new.yaml"
    
    try:
        old_file = request.files.get('oldSpec')
        new_file = request.files.get('newSpec')

        if not old_file or not new_file:
            return jsonify({"success": False, "message": "Both old and new spec files are required."}), 400

        old_file.save(old_file_path)
        new_file.save(new_file_path)

        diff_output = redocly_cli.diff_specs(old_file_path, new_file_path)
        return jsonify({"success": True, "diff": diff_output})

    except subprocess.CalledProcessError as e:
        # `redocly diff` exits with a non-zero code if changes are found.
        # This is expected behavior, so we treat its stdout as a successful result.
        if "Breaking changes" in e.stdout or "Non-breaking changes" in e.stdout or "Total changes" in e.stdout:
             return jsonify({"success": True, "diff": e.stdout})
        # If it's a real error, return the stderr content.
        return jsonify({"success": False, "message": f"Redocly Diff Error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    finally:
        if os.path.exists(old_file_path): os.remove(old_file_path)
        if os.path.exists(new_file_path): os.remove(new_file_path)

