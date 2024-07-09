import os
from dotenv import load_dotenv


load_dotenv()

PROJECTS_DIR = os.path.abspath("projects")
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

UPLOADS_DIR = os.path.join(PROJECTS_DIR, "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)
    
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "SEARXNG").upper()

SEARXNG_URL = os.getenv("SEARXNG_URL", None)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", None)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

SEARCH_RESULTS_LIMIT = int(os.getenv('SEARXNG_RESULTS', '5'))
