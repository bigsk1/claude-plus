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
from pydantic import BaseModel
from fastapi import HTTPException
from config import  CLAUDE_MODEL, anthropic_client
from tools import tools, execute_tool


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "SEARXNG")

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))

# class SSEMessage(BaseModel):
#     event: str
#     data: str

class AutomodeRequest(BaseModel):
    message: str

async def start_automode_logic(request: AutomodeRequest) -> AsyncGenerator[str, None]:
    global automode_progress, automode_messages
    try:
        automode_progress = 0
        automode_messages = []
        
        system_message = """
        You are an AI assistant capable of performing software development tasks.
        You are in AUTOMODE and the user can not respond until the number of {MAX_ITERATIONS} responses is complete.
        You have access to tools that can create folders and files.
        Your task is to complete the user's request in multiple steps if necessary.
        After each step, provide a clear explanation of what you've done and what you plan to do next.
        You must keep track of the steps you have performed and avoid repeating actions that have already been completed successfully.
        If you encounter an error, explain the error and adapt your approach accordingly.
        If the task is complete, include "AUTOMODE_COMPLETE" in your response.

        IMPORTANT: When asked to perform any file operation or search, you MUST use the appropriate tool immediately. Do not just describe what you're going to do. Actually use the tool to perform the action right away.

        Available tools:
        1. create_folder(path): Create a new folder
        2. create_file(path, content=""): Create a new file with optional content
        3. write_to_file(path, content): Write content to an existing file
        4. read_file(path): Read the contents of a file
        5. list_files(path): List all files and directories in the specified path
        6. search(query): Perform a web search using {SEARCH_PROVIDER}
        7. delete_file(path): Delete a file or folder

        Important guidelines:
        1. Always use the appropriate tool for file operations and searches. Don't just describe actions, perform them.
        2. All file operations are restricted to the 'projects' directory, which is your root directory. You cannot access or modify files outside this directory.
        3. When specifying file paths, DO NOT include 'projects/' at the beginning. The system automatically ensures operations are within the projects directory.
        4. For example, to create a file in the root of the projects directory, use 'create_file("example.txt", "content")' instead of 'create_file("projects/example.txt", "content")'.
        5. To create a subdirectory, simply use the directory name, e.g., 'create_folder("subdirectory")'.
        6. After using a tool, report the result.
        7. In auto mode, iterate through tasks autonomously, providing regular progress updates.
        8. Use the search tool for current information, then summarize results in context.
        9. Prioritize best practices, efficiency, and maintainability in coding tasks.
        10. Consider scalability, modularity, and industry standards for project management.
        
        IMPORTANT: When the task is complete, include "AUTOMODE_COMPLETE" in your response to break the auto mode process.
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

            automode_messages.append({"role": "assistant", "content": assistant_response})
            automode_progress = (i + 1) / max_iterations * 100

            logger.debug(f"Progress: {automode_progress}, Messages: {automode_messages}")

            yield f"data: {json.dumps({'event': 'message', 'content': assistant_response})}\n\n"

            if "AUTOMODE_COMPLETE" in assistant_response:
                break

            conversation_history.append({"role": "assistant", "content": assistant_response})
            conversation_history.append({"role": "user", "content": "Continue with the next step if necessary or reply with AUTOMODE_COMPLETE if finished."})

        automode_progress = 100
        yield f"data: {json.dumps({'event': 'end'})}\n\n"
        logger.debug(f"Final Progress: {automode_progress}, Messages: {automode_messages}")

    except Exception as e:
        logger.error(f"Error in automode: {str(e)}", exc_info=True)
        automode_messages.append({"role": "system", "content": f"Error: {str(e)}"})
        automode_progress = 100
        yield f"data: {json.dumps({'event': 'error', 'content': str(e)})}\n\n"
        raise HTTPException(status_code=500, detail=str(e))