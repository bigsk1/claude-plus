FROM mcr.microsoft.com/vscode/devcontainers/python:3.12

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install additional Python packages
RUN pip install --upgrade pip \
    && pip install pylint autopep8 black yapf bandit flake8 mypy pycodestyle

# Set the working directory
WORKDIR /workspace

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Uvicorn
RUN pip install uvicorn

# Set up the entrypoint
COPY .devcontainer/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure correct line endings
RUN sed -i 's/\r$//' /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]