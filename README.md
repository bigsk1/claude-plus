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

   TAVILY_API_KEY=your_tavily_api_key

   SEARXNG_URL=your_searxng_url  # If using SearXNG
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

1. Use the chat interface to communicate with Claude.
2. Upload files or images for analysis.
3. Use the file explorer to manage your project structure.
4. Activate automode for autonomous task completion.
5. Utilize the search functionality for web queries using SEARXNG or Tavily

## Contributing

We welcome contributions to Claude Plus! This project is in active development, and things may change rapidly. Here's how you can contribute:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is under active development. Features may change, and there might be bugs or unexpected behavior. Use at your own risk in production environments.

## Acknowledgments

- Anthropic for the Claude AI model
- Tavily for the search API
- SearXNG for there privacy focus search
- For giving me the idea for building a web version based on the ideas of a cli version https://github.com/Doriandarko/claude-engineer