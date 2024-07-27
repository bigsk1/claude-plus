import os
import logging
import json
from shared_utils import create_file, read_file, write_to_file, create_folder, delete_file, perform_search, list_files, get_safe_path
from config import SEARCH_PROVIDER


logger = logging.getLogger(__name__)

PROJECT_STATE_FILE = "project_state.json"

# Global state to keep track of created folders and files
project_state = {
    "folders": set(),
    "files": set()
}

def clear_state_file():
    global project_state
    project_state = {"folders": set(), "files": set()}
    try:
        if os.path.exists(PROJECT_STATE_FILE):
            os.remove(PROJECT_STATE_FILE)
        logger.info("Project state file cleared")
    except Exception as e:
        logger.error(f"Error clearing project state file: {str(e)}")
    return project_state

def sync_project_state_with_fs():
    global project_state
    try:
        if os.path.exists(PROJECT_STATE_FILE):
            with open(PROJECT_STATE_FILE, "r") as f:
                project_state = json.load(f)
        else:
            project_state = {"folders": set(), "files": set()}
        logger.info("Project state synchronized with file system")
    except Exception as e:
        logger.error(f"Error syncing project state with file system: {str(e)}")

def save_state_to_file(state, filename=PROJECT_STATE_FILE):
    with open(filename, 'w') as f:
        json.dump({"folders": list(state["folders"]), "files": list(state["files"])}, f)

def load_state_from_file(filename=PROJECT_STATE_FILE):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return {"folders": set(data["folders"]), "files": set(data["files"])}
    except FileNotFoundError:
        return {"folders": set(), "files": set()}

# Load the state at the beginning
project_state = load_state_from_file()

tools = [
    {
        "name": "create_folder",
        "description": "Create a new folder at the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path where the folder should be created"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file at the specified path with optional content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path where the file should be created"},
                "content": {"type": "string", "description": "The initial content of the file (optional)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_to_file",
        "description": "Write content to a file at the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the file to write to"},
                "content": {"type": "string", "description": "The full content to write to the file"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the file to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files and directories in the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the folder to list"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete a file at the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the file to delete"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search",
        "description": f"Perform a web search using the {SEARCH_PROVIDER} search provider.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "upload_file",
        "description": "Upload a file to the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "The file to upload (base64 encoded)"}
            },
            "required": ["file"]
        }
    }
]

def execute_tool(tool_name, tool_input):
    try:
        logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")
        result = None

        if tool_name == "create_folder":
            path = str(get_safe_path(tool_input["path"]))
            if path in project_state["folders"]:
                return {"success": True, "result": f"Folder already exists: {tool_input['path']}"}
            result = create_folder(tool_input["path"])
            project_state["folders"].add(path)
        elif tool_name == "create_file":
            path = str(get_safe_path(tool_input["path"]))
            folder_path = os.path.dirname(path)
            if folder_path and folder_path not in project_state["folders"]:
                return {"success": False, "error": f"Folder does not exist: {folder_path}"}
            if path in project_state["files"]:
                return {"success": True, "result": f"File already exists: {tool_input['path']}"}
            result = create_file(tool_input["path"], tool_input.get("content", ""))
            project_state["files"].add(path)
        elif tool_name == "write_to_file":
            path = str(get_safe_path(tool_input["path"]))
            if path not in project_state["files"]:
                return {"success": False, "error": f"File does not exist: {tool_input['path']}"}
            result = write_to_file(tool_input["path"], tool_input["content"])
        elif tool_name == "read_file":
            path = str(get_safe_path(tool_input["path"]))
            result = read_file(tool_input["path"])
            if result.startswith("File not found:") or result.startswith("Error reading file:"):
                return {"success": False, "error": result}
        elif tool_name == "list_files":
            path = str(get_safe_path(tool_input["path"]))
            result = list_files(tool_input["path"])
        elif tool_name == "delete_file":
            path = str(get_safe_path(tool_input["path"]))
            result = delete_file(tool_input["path"])
            project_state["files"].discard(path)
            project_state["folders"].discard(path)
        elif tool_name == "search":
            result = perform_search(tool_input["query"])
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # Save the state to a file after a successful operation
        save_state_to_file(project_state)

        logger.debug(f"Tool result: {result}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Error executing tool {tool_name}: {str(e)}"}