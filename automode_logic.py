# This file is part of Claude Plus.
#
# Claude Plus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Claude Plus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Claude Plus.  If not, see <https://www.gnu.org/licenses/>.
import os
import json
import logging
from typing import AsyncGenerator
from anthropic import Anthropic
from pydantic import BaseModel
from fastapi import HTTPException


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
PROJECTS_DIR = "projects"

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "SEARXNG")

class AutomodeRequest(BaseModel):
    message: str

class SSEMessage(BaseModel):
    event: str
    data: str

def create_folder(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return f"Folder created: {path}"
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}", exc_info=True)
        return f"Error creating folder: {str(e)}"

def create_file(path: str, content: str = "") -> str:
    try:
        full_path = os.path.join(path)
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        with open(full_path, 'w') as file:
            file.write(content)
        return f"File created: {full_path}"
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}", exc_info=True)
        return f"Error creating file: {str(e)}"

def write_to_file(path: str, content: str) -> str:
    try:
        full_path = os.path.join(path)
        with open(full_path, 'w') as file:
            file.write(content)
        return f"File written: {full_path}"
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}", exc_info=True)
        return f"Error writing to file: {str(e)}"

def read_file(path: str) -> str:
    try:
        full_path = os.path.join(path)
        with open(full_path, 'r') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}", exc_info=True)
        return f"Error reading file: {str(e)}"

def list_files(path: str) -> str:
    try:
        full_path = os.path.join(path)
        files = os.listdir(full_path)
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        return f"Error listing files: {str(e)}"

def delete_file(path: str) -> str:
    try:
        full_path = os.path.join(PROJECTS_DIR, path)
        os.remove(full_path)
        return f"File deleted: {full_path}"
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        return f"Error deleting file: {str(e)}"

def search_files(query):
    try:
        # Implement the search logic here
        return f"Search results for query: {query}"
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}", exc_info=True)
        return f"Error searching files: {str(e)}"

def execute_tool(tool_name, tool_input):
    try:
        logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")
        if tool_name == "create_folder":
            result = create_folder(tool_input["path"])
        elif tool_name == "create_file":
            result = create_file(tool_input["path"], tool_input.get("content", ""))
        elif tool_name == "write_to_file":
            result = write_to_file(tool_input["path"], tool_input["content"])
        elif tool_name == "read_file":
            result = read_file(tool_input["path"])
        elif tool_name == "list_files":
            result = list_files(tool_input["path"])
        elif tool_name == "delete_file":
            result = delete_file(tool_input["path"])
        elif tool_name == "search_files":
            result = search_files(tool_input["query"])
        else:
            result = f"Unknown tool: {tool_name}"
        logger.debug(f"Tool result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return f"Error executing tool {tool_name}: {str(e)}"

tools = [
    {
        "name": "create_folder",
        "description": "Create a new folder at the specified path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the folder should be created"
                }
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
                "path": {
                    "type": "string",
                    "description": "The path where the file should be created"
                },
                "content": {
                    "type": "string",
                    "description": "The initial content of the file (optional)"
                }
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
                "path": {
                    "type": "string",
                    "description": "The path of the file to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The full content to write to the file"
                }
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
                "path": {
                    "type": "string",
                    "description": "The path of the file to read"
                }
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
                "path": {
                    "type": "string",
                    "description": "The path of the folder to list"
                }
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
                "path": {
                    "type": "string",
                    "description": "The path of the file to delete"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files and directories based on a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]

async def start_automode_logic(request: AutomodeRequest) -> AsyncGenerator[str, None]:
    try:
        system_message = """
        You are an AI assistant capable of performing software development tasks.
        You have access to tools that can create folders and files.
        Your task is to complete the user's request in multiple steps if necessary.
        After each step, provide a clear explanation of what you've done and what you plan to do next.
        You must keep track of the steps you have performed and avoid repeating actions that have already been completed successfully.
        If you encounter an error, explain the error and adapt your approach accordingly.
        If the task is complete, include "AUTOMODE_COMPLETE" in your response.
        
        IMPORTANT: When asked to perform any file operation or search, you MUST use the appropriate tool immediately. Do not just describe what you're going to do. Actually use the tool to perform the action right away.
        
        Available tools:
        - create_folder(path): Create a new folder at the specified path.
        - create_file(path, content): Create a new file at the specified path with optional content.
        - write_to_file(path, content): Write content to a file at the specified path.
        - read_file(path): Read the contents of a file at the specified path.
        - list_files(path): List all files and directories in the specified path.
        - delete_file(path): Delete a file at the specified path.
        - search(query): Perform a web search using {SEARCH_PROVIDER}
        
        Important guidelines:
        1. Always use the appropriate tool for file operations and searches. Don't just describe actions, perform them.
        2. All file operations are restricted to the 'projects' directory for security reasons. You cannot access or modify files outside this directory.
        3. For file paths, always start with 'projects/'. The system will ensure operations are within this directory.
        4. After using a tool, report the result and ask if further actions are needed.
        5. For uploaded files, analyze the contents immediately without using the read_file tool.
        6. In auto mode, iterate through tasks autonomously, providing regular progress updates.
        7. For image uploads, analyze and describe the contents in detail.
        8. Use the search tool for current information, then summarize results in context.
        9. Prioritize best practices, efficiency, and maintainability in coding tasks.
        10. Consider scalability, modularity, and industry standards for project management.
        """


        conversation_history = [
            {"role": "user", "content": request.message}
        ]

        max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))

        for i in range(max_iterations):
            response = anthropic_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=system_message,
                messages=conversation_history,
                tools=tools
            )

            assistant_response = ""
            for content in response.content:
                if content.type == 'text':
                    assistant_response += content.text + "\n"
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_input = content.input
                    tool_result = execute_tool(tool_name, tool_input)
                    assistant_response += f"Used tool: {tool_name}\nResult: {tool_result}\n\n"

            yield f"data: {json.dumps({'event': 'message', 'content': assistant_response})}\n\n"
            conversation_history.append({"role": "assistant", "content": assistant_response})

            if "AUTOMODE_COMPLETE" in assistant_response:
                break

            conversation_history.append({"role": "user", "content": "Continue with the next step if necessary."})

        yield f"data: {json.dumps({'event': 'end'})}\n\n"

    except Exception as e:
        logger.error(f"Error in automode: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'event': 'error', 'content': str(e)})}\n\n"
        raise HTTPException(status_code=500, detail=str(e))