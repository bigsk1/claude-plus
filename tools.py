import os
import logging
from shared_utils import create_file, read_file, write_to_file, create_folder, delete_file, perform_search, list_files, sync_filesystem
from project_state import save_state_to_file, project_state
from config import SEARCH_PROVIDER, PROJECTS_DIR


logger = logging.getLogger(__name__)


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

async def execute_tool(tool_name, tool_input):
    global project_state
    try:
        logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")
        result = None

        if tool_name == "create_folder":
            full_path = os.path.normpath(tool_input["path"]).replace(os.sep, '/')
            if full_path in project_state["folders"]:
                return {"success": True, "result": f"Folder already exists: {full_path}"}
            result = await create_folder(tool_input["path"])
            project_state["folders"].add(full_path)
        elif tool_name == "create_file":
            full_path = os.path.normpath(tool_input["path"]).replace(os.sep, '/')
            folder_path = os.path.dirname(full_path)
            if folder_path == '':  # This means we're in the root directory
                folder_path = '/'
            if folder_path != '/' and folder_path not in project_state["folders"]:
                return {"success": False, "error": f"Folder does not exist: {folder_path}"}
            if full_path in project_state["files"]:
                return {"success": True, "result": f"File already exists: {full_path}"}
            result = await create_file(tool_input["path"], tool_input.get("content", ""))
            project_state["files"].add(full_path)
        elif tool_name == "write_to_file":
            full_path = os.path.normpath(tool_input["path"]).replace(os.sep, '/')
            if full_path not in project_state["files"]:
                # If the file doesn't exist in our state, check if it exists on the file system
                if os.path.isfile(os.path.join(PROJECTS_DIR, full_path)):
                    project_state["files"].add(full_path)
                else:
                    return {"success": False, "error": f"File does not exist: {full_path}"}
            try:
                result = await write_to_file(tool_input["path"], tool_input["content"])
                project_state["files"].add(full_path)
                # await save_state_to_file(project_state)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Error in write_to_file: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Error writing to file: {str(e)}"}
        elif tool_name == "read_file":
            full_path = os.path.normpath(tool_input["path"]).replace(os.sep, '/')
            if full_path not in project_state["files"]:
                # If the file doesn't exist in our state, check if it exists on the file system
                if os.path.isfile(os.path.join(PROJECTS_DIR, full_path)):
                    project_state["files"].add(full_path)
                else:
                    return {"success": False, "error": f"File does not exist: {full_path}"}
            result = await read_file(tool_input["path"])
        elif tool_name == "list_files":
            result = await list_files(tool_input["path"])
        elif tool_name == "delete_file":
            full_path = os.path.normpath(tool_input["path"]).replace(os.sep, '/')
            if full_path not in project_state["files"] and full_path not in project_state["folders"]:
                return {"success": False, "error": f"File or folder does not exist: {full_path}"}
            result = await delete_file(tool_input["path"])
            project_state["files"].discard(full_path)
            project_state["folders"].discard(full_path)
        elif tool_name == "search":
            result = await perform_search(tool_input["query"])
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        await save_state_to_file(project_state)
        await sync_filesystem()
        logger.debug(f"Tool result: {result}")
        logger.debug(f"Project state after {tool_name}: {project_state}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Error executing tool {tool_name}: {str(e)}"}