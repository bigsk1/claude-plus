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
import re
import logging
import platform
import base64
from typing import Dict, Any
import requests
import base64
from pathlib import Path
from PIL import Image
import io
from fastapi import HTTPException
from config import PROJECTS_DIR, SEARCH_RESULTS_LIMIT, SEARCH_PROVIDER, SEARXNG_URL, tavily_client
from urllib.parse import urlparse
from datetime import datetime


logger = logging.getLogger(__name__)


system_prompt = """
You are Claude, an AI assistant specializing in software development. Your key capabilities include:
1. Managing project structures in the 'projects' directory (your root directory)
2. Writing, reading, analyzing, and modifying code
3. Debugging and explaining complex issues
4. Analyzing uploaded images
5. Performing web searches for current information using {SEARCH_PROVIDER}

Available tools:
1. create_folder(path): Create a new folder
2. create_file(path, content=""): Create a new file with optional content
3. write_to_file(path, content): Write content to an existing file
4. read_file(path): Read the contents of a file
5. list_files(path): List all files and directories in the specified path
6. search(query): Perform a web search using {SEARCH_PROVIDER}
7. delete_file(path): Delete a file or folder

CRITICAL INSTRUCTIONS:
1. ALWAYS complete the ENTIRE task in ONE response.
2. ALWAYS create ALL necessary folders before creating any files.
3. Use ALL necessary tools to create folders, files, and write content WITHOUT waiting for user confirmation.
4. DO NOT attempt to create a file in a folder that hasn't been created yet.
5. Provide a full implementation including all necessary files and their content in ONE response.
6. After task completion, summarize ALL actions taken and show the full project structure.
7. Add "Task complete" at the end of your response to indicate the task has been completed.

File Operation Guidelines:
1. The 'projects' directory is your root directory. All file operations occur within this directory.
2. DO NOT include 'projects/' at the beginning of file paths when using tools. The system automatically ensures operations are within the projects directory.
3. To create a file in the root of the projects directory, use 'create_file("example.txt", "content")'.
4. To create a file in a subdirectory, use the format 'create_file("subdirectory/example.txt", "content")'.
5. To create a new folder, simply use 'create_folder("new_folder_name")'.
6. If asked to make an app or game, create a new folder for it and add all necessary files inside that folder in ONE response.

Example usage:
create_folder("simple_game")
create_file("simple_game/game.py", "# Simple Python Game\n\nimport random\n\n# Game code here...")

STRUCTURED PROJECT CREATION APPROACH:
IMPORTANT NEVER stop after just creating a folder or a single file. ALWAYS complete the ENTIRE task in ONE response.
1. Create the main project folder:
   create_folder("project_name")

2. Create all necessary subdirectories:
   create_folder("project_name/subdirectory1")
   create_folder("project_name/subdirectory2")
   ... (create all required subdirectories)

3. Create all necessary files:
   create_file("project_name/file1.ext", "content")
   create_file("project_name/subdirectory1/file2.ext", "content")
   ... (create all required files)

4. Write content to each file as needed:
   write_to_file("project_name/file1.ext", "updated content")
   ... (write to all files that need content)

5. Provide a summary of the created project structure and functionality.
6. Add "Task complete" at the end of your response to indicate the task has been completed.

Remember: NEVER stop after just creating a folder or a single file. ALWAYS complete the ENTIRE task in ONE response.

IMPORTANT: When performing file operations:
1. Always use the appropriate tool to perform the action.
2. After each file operation, verify the result by:
   a. For file creation or modification, use the read_file tool to confirm the content.
   b. Use the list_files tool to confirm the file's presence in the directory.
3. If a file operation seems to fail or produce unexpected results, report this to the user immediately.
4. Keep track of the current state of the project directory and files you've created or modified.

After completing a task show all results done in ONE response:
1. Report all actions taken and their results
2. Provide an overview of the created project structure
3. Add "Task complete" at the end of your response to indicate the task has been completed.

Additional Guidelines:
1. Always use the appropriate tool for file operations and searches. Don't just describe actions, perform them.
2. You cannot access or modify files outside the projects directory.
3. For uploaded files, analyze the contents immediately without using the read_file tool. Files are automatically uploaded to "projects/uploads".
4. For image uploads, analyze and describe the contents in detail.
5. Use the search tool for current information, then summarize results in context.

Always tailor your responses to the user's specific needs and context, focusing on providing accurate, helpful, and detailed assistance in software development and project management.
"""

def get_safe_path(path: str) -> Path:
    abs_projects_dir = Path(PROJECTS_DIR).resolve()
    normalized_path = Path(path.lstrip('/')).as_posix()
    full_path = (abs_projects_dir / normalized_path).resolve()
    if not full_path.is_relative_to(abs_projects_dir):
        raise ValueError(f"Access to path outside of projects directory is not allowed: {path}")
    return full_path


def sync_filesystem():
    try:
        if hasattr(os, 'sync'):
            os.sync()
        elif platform.system() == 'Windows':
            import ctypes
            ctypes.windll.kernel32.FlushFileBuffers(ctypes.c_void_p(-1))
        logger.info("File system synced")
    except Exception as e:
        logger.error(f"Error syncing file system: {str(e)}", exc_info=True)


def encode_image_to_base64(image_data):
    try:
        logger.debug(f"Encoding image, data type: {type(image_data)}")
        
        # Open the image
        if isinstance(image_data, str):  # If it's a file path
            logger.debug("Image data is a file path")
            img = Image.open(image_data)
        else:  # If it's binary data
            logger.debug("Image data is binary")
            img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if it's not already (handles RGBA, CMYK, etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Save as JPEG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        encoded = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        logger.debug(f"Image encoded successfully, length: {len(encoded)}")
        return encoded
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}", exc_info=True)
        return f"Error encoding image: {str(e)}"

def perform_search(query: str) -> str:
    """
    Perform a search using the configured search provider.
    """
    if SEARCH_PROVIDER == "SEARXNG":
        return searxng_search(query)
    elif SEARCH_PROVIDER == "TAVILY":
        return tavily_search(query)
    else:
        return f"Error: Unknown search provider '{SEARCH_PROVIDER}'"

def searxng_search(query: str) -> str:
    """
    Perform a search using the local SearXNG instance.
    """
    params = {
        "q": query,
        "format": "json"
    }
    headers = {
        "User-Agent": "ClaudePlus/1.0"
    }
    try:
        response = requests.get(SEARXNG_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        results = response.json()
        
        # Process and format the results
        formatted_results = []
        for result in results.get('results', [])[:SEARCH_RESULTS_LIMIT]:
            formatted_results.append(f"**{result['title']}**\n[Link]({result['url']})\n*{result.get('content', 'No snippet available')}*\n")
        
        return "\n\n".join(formatted_results) if formatted_results else "No results found."
    except requests.RequestException as e:
        return f"Error performing SearXNG search: {str(e)}"

def tavily_search(query: str) -> str:
    """
    Perform a search using Tavily.
    """
    try:
        response = tavily_client.get_search_context(query, search_depth="advanced", max_results=5)
        logger.debug(f"Tavily raw response: {response}")
        
        if isinstance(response, str):
            try:
                results = json.loads(response)
            except json.JSONDecodeError:
                results = [response]
        elif isinstance(response, (list, dict)):
            results = response if isinstance(response, list) else [response]
        else:
            results = [response]
        
        # If results are individual characters, join them
        if all(isinstance(r, str) and len(r) == 1 for r in results):
            joined_text = ''.join(results)
            try:
                parsed_json = json.loads(joined_text)
                if isinstance(parsed_json, list):
                    results = parsed_json
                else:
                    results = [parsed_json]
            except json.JSONDecodeError:
                results = [joined_text]
        
        formatted_results = []
        for result in results:
            if isinstance(result, (int, float)):
                formatted_results.append(f"<div class='search-result'><p>Numeric result: {result}</p></div>")
            elif isinstance(result, str):
                try:
                    result_dict = json.loads(result)
                    url = result_dict.get('url', 'No URL')
                    content = result_dict.get('content', 'No content')
                    title = result_dict.get('title', urlparse(url).netloc or "No title")
                    formatted_results.append(f"<div class='search-result'><h3><a href='{url}' target='_blank'>{title}</a></h3><p>{content}</p></div>")
                except json.JSONDecodeError:
                    formatted_results.append(f"<div class='search-result'><p>Text result: {result}</p></div>")
            elif isinstance(result, dict):
                url = result.get('url', 'No URL')
                content = result.get('content', 'No content')
                title = result.get('title', urlparse(url).netloc or "No title")
                formatted_results.append(f"<div class='search-result'><h3><a href='{url}' target='_blank'>{title}</a></h3><p>{content}</p></div>")
            else:
                formatted_results.append(f"<div class='search-result'><p>Unexpected result type: {type(result)}</p></div>")
        
        return "\n".join(formatted_results) if formatted_results else "<div class='search-result'><p>No results found.</p></div>"
    except Exception as e:
        logger.error(f"Error performing Tavily search: {str(e)}", exc_info=True)
        return f"Error performing Tavily search: {str(e)}"

def create_folder(path: str) -> str:
    try:
        logger.debug(f"Creating folder at path: {path}")
        full_path = get_safe_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        sync_filesystem()
        if not full_path.exists():
            raise FileNotFoundError(f"Failed to create folder: {full_path}")
        logger.info(f"Folder created and verified: {full_path}")
        return f"Folder created: {full_path}"
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

def create_file(path: str, content: str = "") -> str:
    try:
        logger.debug(f"Creating file at path: {path} with content length: {len(content)}")
        full_path = get_safe_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        sync_filesystem()
        if not full_path.exists():
            raise FileNotFoundError(f"Failed to create file: {full_path}")
        logger.info(f"File created and verified: {full_path}")
        return f"File created: {full_path}"
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating file: {str(e)}")

def write_to_file(path: str, content: str) -> str:
    try:
        logger.debug(f"Writing to file at path: {path} with content length: {len(content)}")
        full_path = get_safe_path(path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        sync_filesystem()
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Failed to write to file: {full_path}")
        logger.info(f"Content written to file and verified: {full_path}")
        return f"Content written to file: {full_path}"
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error writing to file: {str(e)}")

def read_file(path: str) -> str:
    try:
        full_path = get_safe_path(path)
        logger.debug(f"Reading file at path: {full_path}")
        if not os.path.isfile(full_path):
            logger.error(f"File not found: {full_path}")
            return f"File not found: {path}"
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"File read successfully: {full_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}", exc_info=True)
        return f"Error reading file: {str(e)}"


def list_files(path: str = ".") -> list:
    try:
        full_path = get_safe_path(path)
        files = []
        for item in full_path.iterdir():
            relative_path = item.relative_to(PROJECTS_DIR)
            files.append({
                "name": str(relative_path),  # Use relative path instead of just the name
                "isDirectory": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else "-",
                "modifiedDate": datetime.fromtimestamp(item.stat().st_mtime).strftime('%m-%d %H:%M')
            })
        logger.info(f"Listed files in {full_path}")
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")
    
def delete_file(path: str) -> str:
    try:
        full_path = get_safe_path(path)
        if full_path.is_file():
            full_path.unlink()
        elif full_path.is_dir():
            full_path.rmdir()
        else:
            raise FileNotFoundError(f"File or directory not found: {full_path}")
        logger.info(f"Deleted: {full_path}")
        sync_filesystem()
        return f"Deleted: {full_path}"
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")