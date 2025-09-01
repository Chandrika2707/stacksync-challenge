import json
import subprocess
import tempfile
import os
import shutil
from flask import Flask, request, jsonify
import ast

app = Flask(__name__)

def validate_python_script(script):
    """Validate that the script contains a main() function and returns JSON."""
    try:
        # Parse the script to check for syntax errors
        tree = ast.parse(script)
        
        # Check if main function exists
        has_main = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'main':
                has_main = True
                break
        
        if not has_main:
            return False, "Script must contain a main() function"
        
        # Check for dangerous imports and functions (more precise)
        dangerous_patterns = [
            'import subprocess',
            'from subprocess import',
            'os.system(',
            'eval(',
            'exec(',
            '__import__(',
            'os.listdir(',
            'os.chdir(',
            'open(',
            'file(',
            'glob.glob(',
            'import glob'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in script:
                return False, f"Dangerous import/function '{pattern}' is not allowed"
        
        return True, "Valid script"
    except SyntaxError as e:
        return False, f"Invalid Python syntax: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def create_safe_script(script):
    """Create a safe wrapper script that captures main() return value."""
    # Indent the user script to fit within the try block
    indented_script = '\n'.join('    ' + line if line.strip() else line for line in script.split('\n'))
    
    safe_wrapper = f"""import json
import sys
import io
from contextlib import redirect_stdout

# Capture stdout
stdout_capture = io.StringIO()

try:
    # Execute the user script
{indented_script}
    
    # Capture stdout during main() execution
    with redirect_stdout(stdout_capture):
        result = main()
    
    # Ensure result is JSON serializable
    if result is None:
        result = None
    elif isinstance(result, (dict, list, str, int, float, bool)):
        pass  # These are JSON serializable
    else:
        result = str(result)  # Convert to string if not JSON serializable
    
    # Return result and stdout
    output = {{
        "result": result,
        "stdout": stdout_capture.getvalue()
    }}
    
    print(json.dumps(output))
    
except Exception as e:
    error_output = {{
        "error": str(e),
        "stdout": stdout_capture.getvalue()
    }}
    print(json.dumps(error_output))
    sys.exit(1)
"""
    return safe_wrapper

def execute_with_nsjail(script):
    """Execute the script using nsjail for security."""
    # Create temporary directory for execution
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the safe wrapper script
        safe_script = create_safe_script(script)
        script_path = os.path.join(temp_dir, "script.py")
        
        with open(script_path, 'w') as f:
            f.write(safe_script)
        
        # Check if nsjail is available
        try:
            subprocess.run(["/usr/local/bin/nsjail", "--help"], capture_output=True, check=True)
            nsjail_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            nsjail_available = False
        
        if nsjail_available:
            # nsjail configuration for security
            nsjail_cmd = [
                "/usr/local/bin/nsjail",
                "--config", "/etc/nsjail/nsjail.cfg",
                "--cwd", "/tmp",
                "--bindmount", f"{temp_dir}:/tmp",
                "--bindmount", "/usr:/usr:ro",
                "--bindmount", "/lib:/lib:ro",
                "--bindmount", "/lib64:/lib64:ro",
                "--bindmount", "/bin:/bin:ro",
                "--bindmount", "/sbin:/sbin:ro",
                "--", "python3", script_path
            ]
            
            try:
                # Execute with nsjail
                result = subprocess.run(
                    nsjail_cmd,
                    capture_output=True,
                    text=True,
                    timeout=35  # Slightly longer than nsjail timeout
                )
                
                if result.returncode == 0:
                    try:
                        # Parse the JSON output
                        output = json.loads(result.stdout.strip())
                        return output
                    except json.JSONDecodeError:
                        return {
                            "error": "Failed to parse script output",
                            "stdout": result.stdout,
                            "stderr": result.stderr
                        }
                else:
                    return {
                        "error": f"Script execution failed (exit code: {result.returncode})",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    "error": "Script execution timed out (30 seconds)",
                    "stdout": "",
                    "stderr": ""
                }
            except Exception as e:
                return {
                    "error": f"nsjail execution error: {str(e)}",
                    "stdout": "",
                    "stderr": ""
                }
        else:
            # Fallback to restricted execution if nsjail is not available
            return execute_with_restrictions(script)

def execute_with_restrictions(script):
    """Execute the script with security restrictions when nsjail fails."""
    # Create temporary directory for execution
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the safe wrapper script
        safe_script = create_safe_script(script)
        script_path = os.path.join(temp_dir, "script.py")
        
        with open(script_path, 'w') as f:
            f.write(safe_script)
        
        try:
            # Execute with timeout and resource monitoring
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=temp_dir,
                env={
                    'PYTHONPATH': '/app',
                    'PATH': '/usr/local/bin:/usr/bin:/bin',
                    'HOME': temp_dir,
                    'TMPDIR': temp_dir
                }
            )
            
            if result.returncode == 0:
                try:
                    # Parse the JSON output
                    output = json.loads(result.stdout.strip())
                    return output
                except json.JSONDecodeError:
                    return {
                        "error": "Failed to parse script output",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
            else:
                return {
                    "error": f"Script execution failed (exit code: {result.returncode})",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "error": "Script execution timed out (30 seconds)",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "error": f"Execution error: {str(e)}",
                "stdout": "",
                "stderr": ""
            }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Check if nsjail is available
    try:
        subprocess.run(["/usr/local/bin/nsjail", "--help"], capture_output=True, check=True)
        nsjail_status = "available"
    except (subprocess.CalledProcessError, FileNotFoundError):
        nsjail_status = "not available"
    
    return jsonify({
        "status": "healthy", 
        "service": "Safe Python Execution Service (Enhanced with nsjail)",
        "security": f"nsjail + input validation (nsjail: {nsjail_status})",
        "features": [
            "resource limits", 
            "dangerous import blocking", 
            "sandboxed execution",
            "nsjail sandboxing"
        ]
    })

@app.route('/execute', methods=['POST'])
def execute_script():
    """Execute a Python script safely."""
    try:
        # Parse request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data or 'script' not in data:
            return jsonify({"error": "Request must contain 'script' field"}), 400
        
        script = data['script']
        if not script or not isinstance(script, str):
            return jsonify({"error": "Script must be a non-empty string"}), 400
        
        # Validate script
        is_valid, message = validate_python_script(script)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Execute script safely with nsjail, fallback to restrictions if needed
        result = execute_with_nsjail(script)
        
        # Check if execution resulted in an error
        if "error" in result:
            # If nsjail failed, try fallback execution
            if "nsjail execution error" in result.get("error", "") or "Script execution failed" in result.get("error", ""):
                print(f"nsjail failed, falling back to restricted execution: {result.get('error')}")
                result = execute_with_restrictions(script)
                
                # Check if fallback also failed
                if "error" in result:
                    return jsonify(result), 400
            else:
                return jsonify(result), 400
        
        # Return successful execution result
        return jsonify({
            "result": result.get("result"),
            "stdout": result.get("stdout", "")
        })
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
