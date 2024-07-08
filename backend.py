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
import uvicorn
import logging
from functools import wraps
from typing import Callable
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from config import PROJECTS_DIR, UPLOADS_DIR, SEARCH_PROVIDER
from automode_logic import start_automode_logic, AutomodeRequest
from shared_utils import (
    anthropic_client, system_prompt,
    perform_search, encode_image_to_base64, create_folder, create_file,
    read_file, list_files, list_files_frontend, delete_file, read_file_frontend, delete_file_frontend, create_file_frontend,
    write_to_file_frontend, create_folder_frontend, write_to_file
)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Available endpoints:")
    for route in app.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                logger.info(f"{method} {route.path}")
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

# Conversation history
conversation_history = []

# # Automode flag
# automode = False


# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None

# class AutomodeRequest(BaseModel):
#     message: str
#     max_iterations: int = 5

class SearchQuery(BaseModel):
    query: str

class ProjectRequest(BaseModel):
    template: str
    
class CreateFileRequest(BaseModel):
    path: str
    content: str = ""

class FilePath(BaseModel):
    path: str
    content: Optional[str] = None


def is_safe_path(path: str) -> bool:
    abs_projects_dir = os.path.abspath(PROJECTS_DIR)
    abs_path = os.path.abspath(os.path.join(PROJECTS_DIR, path))
    return os.path.commonpath([abs_projects_dir, abs_path]) == abs_projects_dir

def safe_path_operation(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        path = kwargs.get('path', '.')
        full_path = os.path.abspath(os.path.join(PROJECTS_DIR, path))
        print(f"[DEBUG] safe_path_operation: original_path={path}, full_path={full_path}")
        if not full_path.startswith(PROJECTS_DIR):
            raise HTTPException(status_code=403, detail="Access to this directory is not allowed")
        
        kwargs['path'] = os.path.relpath(full_path, PROJECTS_DIR)
        print(f"[DEBUG] safe_path_operation: adjusted_path={kwargs['path']}")
        return await func(*args, **kwargs)
    return wrapper


@app.post("/automode")
async def start_automode(request: Request):
    automode_request = AutomodeRequest(**await request.json())
    return StreamingResponse(start_automode_logic(automode_request), media_type="text/event-stream")

@app.get("/automode")
async def start_automode_get(message: str):
    automode_request = AutomodeRequest(message=message)
    return StreamingResponse(start_automode_logic(automode_request), media_type="text/event-stream")


@app.post("/create_project")
@safe_path_operation
async def create_project(request: ProjectRequest, path: str):
    try:
        project_name = f"{request.template.lower()}_project"
        project_path = os.path.join(PROJECTS_DIR, path, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        if request.template == "react":
            create_file(os.path.join(project_path, "package.json"), '{"name": "react-app", "version": "1.0.0"}')
            create_file(os.path.join(project_path, "src/App.js"), 'import React from "react";\n\nfunction App() {\n  return <div>Hello, React!</div>;\n}\n\nexport default App;')
        elif request.template == "node":
            create_file(os.path.join(project_path, "package.json"), '{"name": "node-app", "version": "1.0.0"}')
            create_file(os.path.join(project_path, "index.js"), 'console.log("Hello, Node.js!");')
        elif request.template == "python":
            create_file(os.path.join(project_path, "main.py"), 'print("Hello, Python!")')
            create_file(os.path.join(project_path, "requirements.txt"), '')
        else:
            raise ValueError(f"Unknown project template: {request.template}")
        
        return {"message": f"{request.template} project created successfully at {os.path.relpath(project_path, PROJECTS_DIR)}"}
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")


@app.get("/list_files")
@safe_path_operation
async def get_file_list(path: str = Query(...)):
    logger.debug(f"Received path: {path}")
    files = list_files_frontend(path)
    if not files and path:
        raise HTTPException(status_code=404, detail="Directory not found")
    return {"files": files, "currentDirectory": path}


@app.post("/create_folder")
@safe_path_operation
async def create_folder_endpoint(path: str = Query(...)):
    result = create_folder_frontend(path)
    if "Error" in result:
        raise HTTPException(status_code=500, detail=result)
    return {"message": result}

@app.post("/create_file")
@safe_path_operation
async def create_file_endpoint(path: str = Query(...), content: str = ""):
    logger.debug(f"Received path: {path}")
    result = create_file_frontend(path, content)
    if "Error" in result:
        raise HTTPException(status_code=500, detail=result)
    return {"message": result}

@app.get("/read_file")
@safe_path_operation
async def read_file_endpoint(path: str = Query(...)):
    logger.debug(f"Received path: {path}")
    content = read_file_frontend(path)
    if "Error" in content:
        raise HTTPException(status_code=404, detail=content)
    return {"content": content}

@app.post("/write_file")
async def write_file_endpoint(request: Request, path: str = Query(...)):
    try:
        logger.debug(f"Received path: {path}")
        try:
            body = await request.json()
            logger.debug(f"Received body: {body}")
        except Exception as e:
            logger.error(f"Error parsing JSON body: {str(e)}")
            raise HTTPException(status_code=422, detail="Invalid JSON body")

        content = body.get("content", "")
        if not content:
            raise HTTPException(status_code=422, detail="Content is required")

        result = write_to_file_frontend(path, content)
        if "Error" in result:
            raise HTTPException(status_code=500, detail=result)
        return JSONResponse(content={"message": result})
    except Exception as e:
        logger.error(f"Error in write_file_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/delete_file")
@safe_path_operation
async def delete_file_endpoint(path: str = Query(...)):
    logger.debug(f"Received path: {path}")
    result = delete_file_frontend(path)
    if "Error" in result:
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Read the file contents
        with open(file_path, "r") as f:
            file_contents = f.read()
        
        return {
            "message": f"File {file.filename} uploaded successfully to uploads directory",
            "file_contents": file_contents
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        logger.debug(f"Received file: {file.filename}, content_type: {file.content_type}")
        contents = await file.read()
        logger.debug(f"File contents read, length: {len(contents)} bytes")
        
        encoded_image = encode_image_to_base64(contents)
        logger.debug(f"Image encoded, length: {len(encoded_image)}")
        
        if encoded_image.startswith("Error encoding image:"):
            raise ValueError(encoded_image)
        
        analysis_result = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            system=system_prompt,  # Use system parameter instead of including it in messages
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": file.content_type,
                                "data": encoded_image
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyze this image and describe what you see."
                        }
                    ]
                }
            ]
        )
        logger.debug("Analysis result received from Anthropic API")
        return {"analysis": analysis_result.content[0].text}
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")

@app.post("/search")
async def search(query: SearchQuery):
    try:
        results = perform_search(query.query)
        logger.info(f"Search results: {results}")
        return JSONResponse(content={"results": results})
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}", exc_info=True)
        error_details = f"{type(e).__name__}: {str(e)}"
        if hasattr(e, '__traceback__'):
            import traceback
            error_details += f"\nTraceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
        raise HTTPException(status_code=500, detail=f"Error performing search: {error_details}")



# System prompt update function
# def update_system_prompt(current_iteration, max_iterations):
#     return f"""
#     You are Claude, an AI assistant specializing in software development. Your task is to assist with any programming or development task requested by the user. You MUST use the available tools to create files, write code, and manage project structures as needed.

#     You are currently in automode, on iteration {current_iteration} out of {max_iterations}.

#     Important guidelines:
#     1. Always use the appropriate tool for file operations. Don't just describe actions, perform them using the tools provided.
#     2. After using a tool, analyze the result and determine if further actions are needed.
#     3. Adapt your approach based on the specific task requested by the user.
#     4. Provide clear explanations of your actions and any code you write.
#     5. You must use at least one tool in each iteration unless the task is complete.
#     6. If you need to create or modify a file, use the create_file or write_to_file tool.
#     7. If you need to check the contents of a file or directory, use the read_file or list_files tool.

#     Available tools:
#     - create_folder(path): Create a new folder
#     - create_file(path, content): Create a new file with content
#     - write_to_file(path, content): Write or update content in a file
#     - read_file(path): Read the contents of a file
#     - list_files(path): List all files and directories in the specified path

#     When you've completed the requested task or reached a logical stopping point, include "AUTOMODE_COMPLETE" in your response.
#     """

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    global conversation_history, automode
    try:
        message = request.message
        conversation_history.append({"role": "user", "content": message})
        
        logger.info(f"Sending message to AI: {message}")
        response = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,  # Adjust this value if necessary
            system=system_prompt,
            messages=conversation_history,
            tools=tools
        )
        
        logger.info(f"AI response: {response.content}")
        
        response_content = ""
        for content in response.content:
            if content.type == 'text':
                logger.info(f"Text response: {content.text}")
                response_content += content.text
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_input = content.input
                logger.info(f"Tool used: {tool_name}, Input: {tool_input}")
                tool_result = execute_tool(tool_name, tool_input)
                response_content += f"\nTool used: {tool_name}\nTool result: {tool_result}\n"
                logger.info(f"Tool result: {tool_result}")
                # Add a follow-up message based on the tool used
                if tool_name == "read_file" and "The file is empty." in tool_result:
                    response_content += "\nIt seems the file is empty. Would you like to add some content to it?"
                elif tool_name == "write_to_file":
                    response_content += "\nI have successfully written the content to the file. Is there anything else you would like to do?"

        conversation_history.append({"role": "assistant", "content": response_content})
        return {"response": response_content}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/automode")
# async def start_automode(request: AutomodeRequest):
#     global conversation_history
#     responses = []
#     iteration_count = 0
#     max_iterations = request.max_iterations

#     try:
#         conversation_history = []
#         system_prompt = update_system_prompt(current_iteration=1, max_iterations=max_iterations)

#         while iteration_count < max_iterations:
#             logger.info(f"Automode iteration {iteration_count + 1}/{max_iterations}")

#             message = request.message if iteration_count == 0 else "Continue with the next step of the task."
#             conversation_history.append({"role": "user", "content": message})

#             response = anthropic_client.messages.create(
#                 model=CLAUDE_MODEL,
#                 max_tokens=3000,
#                 system=system_prompt,
#                 messages=conversation_history,
#                 tools=tools
#             )

#             logger.debug(f"Received response: {response}")

#             assistant_response = ""
#             tool_used = False
#             tool_result_content = None

#             for content in response.content:
#                 logger.debug(f"Processing content block: {content}")
#                 if content.type == "text":
#                     assistant_response += content.text
#                 elif content.type == "tool_use":
#                     tool_used = True
#                     tool_name = content.name
#                     tool_input = content.input  # content.input is already a dict
#                     logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
#                     tool_result = execute_tool(tool_name, tool_input)
#                     tool_result_content = {
#                         "role": "user",
#                         "content": {
#                             "type": "tool_result",
#                             "tool_use_id": content.id,
#                             "result": tool_result
#                         }
#                     }
#                     assistant_response += f"\nTool used: {tool_name}\nTool result: {tool_result}\n"

#             if assistant_response:
#                 conversation_history.append({"role": "assistant", "content": assistant_response})
#                 responses.append(assistant_response)

#             if "AUTOMODE_COMPLETE" in assistant_response:
#                 logger.info("Automode completed early")
#                 break

#             if tool_used and tool_result_content:
#                 logger.info(f"Appending tool result content: {tool_result_content}")
#                 conversation_history.append(tool_result_content)
#                 follow_up_response = anthropic_client.messages.create(
#                     model=CLAUDE_MODEL,
#                     max_tokens=3000,
#                     system=system_prompt,
#                     messages=conversation_history,
#                     tools=tools
#                 )
#                 follow_up_assistant_response = ""
#                 for follow_up_content in follow_up_response.content:
#                     logger.debug(f"Processing follow-up content block: {follow_up_content}")
#                     if follow_up_content.type == "text":
#                         follow_up_assistant_response += follow_up_content.text
#                 if follow_up_assistant_response:
#                     conversation_history.append({"role": "assistant", "content": follow_up_assistant_response})
#                     responses.append(follow_up_assistant_response)

#             iteration_count += 1
#             system_prompt = update_system_prompt(current_iteration=iteration_count + 1, max_iterations=max_iterations)

#         logger.info(f"Automode completed after {iteration_count} iterations")
#         return {"responses": responses}
#     except AnthropicError as e:
#         logger.error(f"Error in automode: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Error in automode: {str(e)}")
#     except Exception as e:
#         logger.error(f"Error in automode: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

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
        elif tool_name == "search":
            result = perform_search(tool_input["query"])
        else:
            result = f"Unknown tool: {tool_name}"
        logger.debug(f"Tool result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return f"Error executing tool {tool_name}: {str(e)}"



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
