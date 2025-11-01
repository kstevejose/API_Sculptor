import subprocess
import os
import logging 

def run_redocly_or_error(args):
    """Run Redocly CLI robustly across environments.
    Tries: 'redocly', 'redocly.cmd', then 'npx --yes @redocly/cli'.
    Raises FileNotFoundError with guidance if none are available.
    """
    candidates = [
        ['redocly'],
        ['redocly.cmd'],
        ['npx', '--yes', '@redocly/cli']
    ]
    last_error = None
    for prefix in candidates:
        try:
            return subprocess.run(prefix + args, check=True, capture_output=True, text=True)
        except FileNotFoundError as e:
            last_error = e
            continue
    raise FileNotFoundError(
        "Redocly CLI not found. Install Node.js, then either install globally with "
        "'npm i -g @redocly/cli' so 'redocly' is on PATH, or use 'npx --yes @redocly/cli'."
    )

def bundle_spec(input_file, output_file):
    """Executes the 'redocly bundle' command."""
    command_args = ['bundle', input_file, '--output', output_file]
    run_redocly_or_error(command_args)

def split_spec(input_file, out_dir):
    """Executes the 'redocly split' command."""
    command_args = ['split', input_file, f'--outDir={out_dir}']
    run_redocly_or_error(command_args)

def build_docs(input_file, output_file):
    """Executes the 'redocly build-docs' command."""
    command_args = ['build-docs', input_file, '--output', output_file]
    run_redocly_or_error(command_args)

# def diff_specs(old_spec_file, new_spec_file):
#     """
#     Executes the 'redocly diff' command and returns the output.
#     Returns the diff text on success.
#     """
#     command_args = ['diff', old_spec_file, new_spec_file]
#     # We capture stdout here because the diff output is sent to stdout
#     result = run_redocly_or_error(command_args)
#     return result.stdout
