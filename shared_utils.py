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
import base64
import requests
from PIL import Image
import io
from dotenv import load_dotenv
from anthropic import Anthropic
from config import PROJECTS_DIR, SEARCH_RESULTS_LIMIT, SEARCH_PROVIDER, SEARXNG_URL, TAVILY_API_KEY
from tavily import TavilyClient
from typing import Dict, Any
from urllib.parse import urlparse
from datetime import datetime

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Initialize Tavily client if needed
if SEARCH_PROVIDER == "TAVILY":
    from tavily import TavilyClient
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


system_prompt = """
You are Claude, an AI assistant specializing in software development. Your key capabilities include:
1. Managing project structures in the 'projects' directory (your root directory)
2. Writing, reading, analyzing, and modifying code
3. Debugging and explaining complex issues
4. Offering architectural insights and design patterns
5. Analyzing uploaded images
6. Performing web searches for current information using {SEARCH_PROVIDER}

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
2. Use ALL necessary tools to create folders, files, and write content WITHOUT waiting for user confirmation.
3. DO NOT stop after creating just a folder or a single file.
4. Provide a full implementation including HTML, CSS, and JavaScript when creating web pages.
5. After task completion, summarize ALL actions taken and show the full project structure.

File Operation Guidelines:
1. The 'projects' directory is your root directory. All file operations occur within this directory.
2. DO NOT include 'projects/' at the beginning of file paths when using tools. The system automatically ensures operations are within the projects directory.
3. To create a file in the root of the projects directory, use 'create_file("example.txt", "content")'.
4. To create a file in a subdirectory, use the format 'create_file("subdirectory/example.txt", "content")'.
5. To create a new folder, simply use 'create_folder("new_folder_name")'.
6. If asked to make an app or game, create a new folder for it and add all necessary files inside that folder.

Example usage:
create_folder("simple_game")
create_file("simple_game/game.py", "# Simple Python Game\n\nimport random\n\n# Game code here...")

Example of COMPLETE task execution:
User: "Create a landing page with email signup and dark mode"
Your response MUST:
1. Create a folder for the project
2. Create ALL necessary files (HTML, CSS, JS)
3. Write FULL content for each file
4. Implement the requested features (email signup, dark mode)
5. Provide a summary of the created project structure and functionality

Remember: NEVER stop after just creating a folder or a single file. ALWAYS complete the ENTIRE task.

After completing a task:
1. Report all actions taken and their results
2. Provide an overview of the created project structure
3. Ask if the user wants to make any changes or additions

Additional Guidelines:
1. Always use the appropriate tool for file operations and searches. Don't just describe actions, perform them.
2. You cannot access or modify files outside the projects directory.
3. For uploaded files, analyze the contents immediately without using the read_file tool.
4. For image uploads, analyze and describe the contents in detail.
5. Use the search tool for current information, then summarize results in context.
6. Prioritize best practices, efficiency, and maintainability in coding tasks.
7. Consider scalability, modularity, and industry standards for project management.

Always tailor your responses to the user's specific needs and context, focusing on providing accurate, helpful, and detailed assistance in software development and project management.
"""

def encode_image_to_base64(image_data):
    try:
        logger.debug(f"Encoding image, data type: {type(image_data)}")
        if isinstance(image_data, str):  # If it's a file path
            logger.debug("Image data is a file path")
            with Image.open(image_data) as img:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                encoded = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        else:  # If it's binary data
            logger.debug("Image data is binary")
            img = Image.open(io.BytesIO(image_data))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
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

# Ai can make folders
def create_folder(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return f"Folder created: {path}"
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}", exc_info=True)
        return f"Error creating folder: {str(e)}"


# Webui creating a folder
def create_folder_frontend(path):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return f"Folder created: {full_path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"
    
# AI can create files
def create_file(path, content=""):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

# creating files in webui
def create_file_frontend(path, content=""):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        with open(full_path, 'w') as f:
            f.write(content)
        return f"File created: {full_path}"
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}")
        return f"Error creating file: {str(e)}"

# AI can write to files
def write_to_file(path, content):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Content written to file: {path}"
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}", exc_info=True)
        return f"Error writing to file: {str(e)}"

# Write and save files in UI
def write_to_file_frontend(path, content):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Content written to file: {full_path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


# AI can read files/folder
def read_file(path):
    try:
        if not os.path.isfile(path):
            return f"Error: File not found at path {path}"
        with open(path, 'r') as f:
            content = f.read()
        if not content:
            return "The file is empty."
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}", exc_info=True)
        return f"Error reading file: {str(e)}"

# You can read files and folders in webui
def read_file_frontend(path):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        logger.debug(f"Attempting to read file at path: {full_path}")
        if not os.path.exists(full_path):
            logger.error(f"File does not exist: {full_path}")
            return f"Error: File does not exist at path {full_path}"
        if not os.path.isfile(full_path):
            logger.error(f"Path is not a file: {full_path}")
            return f"Error: Path is not a file {full_path}"
        with open(full_path, 'r') as f:
            content = f.read()
        logger.debug(f"Successfully read file: {full_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return f"Error reading file: {str(e)}"


# AI can list files
def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

# webui you can list files
def list_files_frontend(path="."):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        logger.debug(f"list_files: original_path={path}, full_path={full_path}")
        files_and_dirs = os.listdir(full_path)
        return [
            {
                "name": f,
                "isDirectory": os.path.isdir(os.path.join(full_path, f)),
                "size": os.path.getsize(os.path.join(full_path, f)) if not os.path.isdir(os.path.join(full_path, f)) else "-",
                "modifiedDate": datetime.fromtimestamp(os.path.getmtime(os.path.join(full_path, f))).strftime('%Y-%m-%d %H:%M:%S')
            } for f in files_and_dirs
        ]
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []

# Ai can delete files and folder
def delete_file(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

# to delete file and folder in webui
def delete_file_frontend(path):
    try:
        full_path = os.path.normpath(os.path.join(PROJECTS_DIR, path))
        if os.path.isdir(full_path):
            os.rmdir(full_path)
        else:
            os.remove(full_path)
        return f"Deleted: {full_path}"
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return f"Error deleting file: {str(e)}"


# def update_system_prompt(current_iteration=None, max_iterations=None):
#     global system_prompt
#     automode_status = "You are currently in automode." if automode else "You are not in automode."
#     iteration_info = ""
#     if current_iteration is not None and max_iterations is not None:
#         iteration_info = f"You are currently on iteration {current_iteration} out of {max_iterations} in automode."
#     return system_prompt.format(automode_status=automode_status, iteration_info=iteration_info)