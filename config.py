import os
from anthropic import Anthropic
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", None)

SEARXNG_URL = os.getenv("SEARXNG_URL", None)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

SEARCH_RESULTS_LIMIT = int(os.getenv('SEARXNG_RESULTS', '5'))


SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "SEARXNG").upper()


tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Initialize Tavily client if needed
if SEARCH_PROVIDER == "TAVILY":
    from tavily import TavilyClient
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROJECTS_DIR = os.path.abspath("projects")
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

UPLOADS_DIR = os.path.join(PROJECTS_DIR, "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)