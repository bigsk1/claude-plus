import os
import logging
import json
from pathlib import Path
from config import PROJECTS_DIR

logger = logging.getLogger(__name__)

PROJECT_STATE_FILE = "project_state.json"

# Global state to keep track of created folders and files
project_state = {
    "folders": set(),
    "files": set()
}

async def clear_state_file():
    global project_state
    project_state = {"folders": set(), "files": set()}
    try:
        if os.path.exists(PROJECT_STATE_FILE):
            os.remove(PROJECT_STATE_FILE)
        logger.info("Project state file cleared")
    except Exception as e:
        logger.error(f"Error clearing project state file: {str(e)}")
    return project_state

async def sync_project_state_with_fs():
    global project_state
    project_state = {"folders": set(), "files": set()}
    
    for root, dirs, files in os.walk(PROJECTS_DIR):
        for dir in dirs:
            rel_path = os.path.relpath(os.path.join(root, dir), PROJECTS_DIR).replace(os.sep, '/')
            project_state["folders"].add(rel_path)
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), PROJECTS_DIR).replace(os.sep, '/')
            project_state["files"].add(rel_path)
    
    await save_state_to_file(project_state)
    logger.debug(f"Synced project state with file system: {project_state}")
    return project_state

async def update_project_state(path: str, is_folder: bool, is_delete: bool = False):
    global project_state
    try:
        # Normalize the path and make it relative to PROJECTS_DIR
        normalized_path = os.path.normpath(path).lstrip(os.sep).replace('\\', '/')
        projects_dir_path = Path(PROJECTS_DIR)
        full_path = projects_dir_path / normalized_path

        # Ensure the path is within PROJECTS_DIR
        try:
            rel_path = str(full_path.relative_to(projects_dir_path))
        except ValueError:
            logger.error(f"Path '{full_path}' is not within PROJECTS_DIR '{projects_dir_path}'")
            return

        logger.debug(f"Updating project state for path: {rel_path}")

        if is_delete:
            project_state["folders"].discard(rel_path)
            project_state["files"].discard(rel_path)
            logger.debug(f"Removed {'folder' if is_folder else 'file'} from project state: {rel_path}")
        else:
            if is_folder:
                project_state["folders"].add(rel_path)
                logger.debug(f"Added folder to project state: {rel_path}")
            else:
                project_state["files"].add(rel_path)
                logger.debug(f"Added file to project state: {rel_path}")

        await save_state_to_file(project_state)
        logger.debug(f"Project state after update: {project_state}")
    except Exception as e:
        logger.error(f"Error updating project state: {str(e)}", exc_info=True)


async def save_state_to_file(state, filename=PROJECT_STATE_FILE):
    with open(filename, 'w') as f:
        json.dump({"folders": list(state["folders"]), "files": list(state["files"])}, f)
    logger.debug(f"Saved project state to file: {state}")
    return state  # Return the state to ensure it's not modified

async def load_state_from_file(filename=PROJECT_STATE_FILE):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return {"folders": set(data["folders"]), "files": set(data["files"])}
    except FileNotFoundError:
        return {"folders": set(), "files": set()}

async def initialize_project_state():
    global project_state
    project_state = await load_state_from_file()
    logger.info("Project state initialized")

async def refresh_project_state():
    global project_state
    project_state = {"folders": set(), "files": set()}

    for root, dirs, files in os.walk(PROJECTS_DIR):
        for dir_name in dirs:
            project_state["folders"].add(os.path.relpath(os.path.join(root, dir_name), PROJECTS_DIR).replace('\\', '/'))
        for file_name in files:
            project_state["files"].add(os.path.relpath(os.path.join(root, file_name), PROJECTS_DIR).replace('\\', '/'))

    await save_state_to_file(project_state)
