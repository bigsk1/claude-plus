import logging
from shared_utils import create_file, read_file, write_to_file, create_folder, delete_file, perform_search, list_files
from config import SEARCH_PROVIDER


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

def execute_tool(tool_name, tool_input):
    try:
        logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")
        result = None
        if tool_name == "create_folder":
            result = create_folder(tool_input["path"])
        elif tool_name == "create_file":
            result = create_file(tool_input["path"], tool_input.get("content", ""))
        elif tool_name == "write_to_file":
            result = write_to_file(tool_input["path"], tool_input["content"])
        elif tool_name == "read_file":
            result = read_file(tool_input["path"])
            if result.startswith("File not found:") or result.startswith("Error reading file:"):
                return {"success": False, "error": result}
        elif tool_name == "list_files":
            result = list_files(tool_input["path"])
        elif tool_name == "delete_file":
            result = delete_file(tool_input["path"])
        elif tool_name == "search":
            result = perform_search(tool_input["query"])
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        logger.debug(f"Tool result: {result}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Error executing tool {tool_name}: {str(e)}"}