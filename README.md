# Claude Plus : AI-Powered Development Assistant

Claude Plus is an advanced AI-powered development assistant that combines the capabilities of Anthropic's Claude AI with a suite of development tools. It's designed to help developers with various tasks, from coding to project management, all through an interactive chat interface.


![Claude-plus](https://imagedelivery.net/WfhVb8dSNAAvdXUdMfBuPQ/88df81c1-27b7-4713-1715-228915742600/public)


## Features

- 🩸 Interact with the enigmatic Claude-3.5-Sonnet
- 🕳️ Manipulate the shadowy file system (create ominous folders, files, read/write cryptic files)
- 👁️‍🗨️ Unearth secrets via Tavily API or SearXNG
- ⚡ Illuminate dark code snippets
- 🕸️ Weave complex project structures
- 🧩 Analyze and suggest improvements with an unsettling precision
- 👁️‍🗨️ Unveil hidden visions with spectral image support
- 🕹️ Automode for eerie, autonomous task completion
- 🔄 Trace iterative changes in automode with chilling accuracy
- 🩸 Diff-based file editing for cold and precise modifications


## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key
- Tavily API key or SearXNG server

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/bigsk1/claude-plus.git
   cd claude-plus
   ```

2. Set up the backend:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Set up the frontend:

   ```
   cd frontend
   npm install
   ```

4. Create a `.env` file in the root directory and add your API keys:

   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key

   CLAUDE_MODEL=claude-3-5-sonnet-20240620

   TAVILY_API_KEY=your_tavily_api_key

   SEARXNG_URL=your_searxng_url  # If using SearXNG

   SEARXNG_URL=http://localhost:4000
   ```

### Running the Application

1. Start the backend server:

   ```
   uvicorn backend:app --reload --host 0.0.0.0 --port 8000
   ```

2. In a new terminal, start the frontend development server from the frontend folder:

   ```
   cd frontend
   npm start
   ```

3. Open your browser and navigate to `http://localhost:5173/`

## Usage

Claude Plus offers a powerful suite of features to enhance your development workflow. Here's how to make the most of this AI-powered assistant:

### 1. Interactive Chat Interface

- **Engage with Claude**: Use the chat interface to communicate with Claude, your AI development assistant.
- **Natural Language Queries**: Ask questions, request code explanations, or seek advice on best practices.
- **Code Generation**: Describe the functionality you need, and Claude will generate code snippets or entire files.
- **Debugging Assistance**: Paste error messages or problematic code for Claude to analyze and suggest fixes.

### 2. File and Image Management

- **File Upload**: Easily upload files for Claude to analyze or work with. All uploaded files are stored in the `projects/uploads` folder.
- **Image Analysis**: Upload images for Claude to describe and analyze, useful for UI/UX discussions or diagram interpretations.
- **Code Review**: Upload your code files for Claude to review, suggest improvements, or explain complex sections.

### 3. Project Structure Management

- **File Explorer**: Use the intuitive file explorer interface to manage your project structure directly in the UI.
- **Create**: Add new files or folders to organize your project.
- **Edit**: Modify existing files with syntax highlighting for various programming languages.
- **Delete**: Remove unnecessary files or folders to keep your project clean.
- **Real-time Updates**: All changes in the file explorer are immediately reflected in the `projects` folder.

### 4. Automode for Autonomous Development

- **Activate Automode**: Enable Claude to work autonomously on complex tasks or entire project setups.
- **Project Generation**: Describe a project idea, and watch as Claude creates folder structures, files, and boilerplate code.
- **Iterative Development**: Claude can refine and expand code over multiple iterations without constant user input.
- **Progress Tracking**: Monitor Claude's progress as it works through tasks in automode.
- **Sandbox Environment**: All automode operations are confined to the `projects` folder, ensuring safe experimentation.

### 5. Web Search Integration

- **Integrated Search**: Perform web searches without leaving the chat interface.
- **Multiple Providers**: Choose between SEARXNG (for privacy-focused searches) or Tavily (for AI-enhanced results).
- **Rich Markdown Display**: Search results are presented in a readable, formatted markdown style.
- **Context-Aware Queries**: Claude can perform searches based on your conversation context for more relevant results.

### 6. Code Execution and Testing (Coming Soon)

- **Secure Sandbox**: Run Python scripts directly within the chat interface.
- **Output Display**: View the results of your code execution inline with your conversation.
- **Interactive Debugging**: Step through code with Claude's guidance to identify and fix issues.

### 7. Version Control Integration (Coming Soon)

- **Git Commands**: Perform basic git operations like commit, push, and pull directly from the chat.
- **Diff Viewer**: Visualize code changes with an integrated diff tool.
- **Commit Message Assistance**: Let Claude suggest meaningful commit messages based on your changes.
 
- **Chat History**: Review past conversations and decisions with a searchable chat history.


Remember, Claude Plus is continuously learning and improving. Don't hesitate to experiment with different approaches and let us know about your experience!

## Docker

This project includes a Docker configuration

### Development Docker Setup

1. Ensure Docker and Docker Compose are installed on your system.
2. Navigate to the project root directory.
3. Build and run the development containers:

   ```
   docker-compose -f docker/docker-compose.dev.yml up -d --build
   ```

4. Access the application:

   - Frontend: http://localhost:5173

The development setup includes hot-reloading for both frontend and backend, and maps the `projects` folder to persist data.


## VS Code Dev Container Setup

This project also includes a configuration for development using VS Code's Remote - Containers extension.

### Prerequisites

- Visual Studio Code
- Docker Desktop
- Remote - Containers extension for VS Code

### Setup

1. Open the project folder in VS Code.
2. When prompted, click "Reopen in Container", or use the Command Palette (F1) and select "Remote-Containers: Reopen in Container".
3. VS Code will build the dev container and reload the window with the project open inside the container.

### Features

- Python 3.12 and Node.js 18 pre-installed
- All project dependencies automatically installed
- Pre-configured linting and formatting tools
- Automatic port forwarding for backend (8000) and frontend (5173)
- Unified development environment across different machines

### Usage

Once inside the dev container:

1. The backend server will start automatically on port 8000.
2. The frontend development server will start automatically on port 5173.
3. You can edit files as normal, and changes will be reflected immediately due to volume mounting.
4. Use the integrated terminal in VS Code to run additional commands if needed.

Note: The first time you open the project in the dev container, it may take a few minutes to build. Subsequent loads will be much faster.


## Contributing

We welcome contributions to Claude Plus! This project is in active development, and things may change rapidly and break and be buggy! Here's how you can contribute:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to test all your features so they do not inadvertently cause another issue.


## Disclaimer

This project is under active development. Features may change, and there might be bugs or unexpected behavior. Use at your own risk in production environments.

## Acknowledgments

- Anthropic for the Claude AI model
- Tavily for the search API
- SearXNG for there privacy focus search
- For giving me the idea for building a web version based on the ideas of a cli version https://github.com/Doriandarko/claude-engineer