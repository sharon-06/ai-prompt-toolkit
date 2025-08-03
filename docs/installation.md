# Installation Guide

This guide covers all installation methods for the AI Prompt Toolkit, from simple pip installation to advanced deployment scenarios.

## 📋 Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB+ recommended for optimization)
- **Storage**: 2GB free space

### Optional Dependencies

- **Redis**: For distributed caching (recommended for production)
- **PostgreSQL**: For production database (SQLite used by default)
- **Docker**: For containerized deployment
- **Ollama**: For local LLM testing

## 🚀 Quick Installation

### Method 1: pip (Recommended)

```bash
# Install the latest stable version
pip install ai-prompt-toolkit

# Install with all optional dependencies
pip install ai-prompt-toolkit[all]

# Install specific extras
pip install ai-prompt-toolkit[redis,postgres,monitoring]
```

### Method 2: conda

```bash
# Install from conda-forge
conda install -c conda-forge ai-prompt-toolkit

# Or create a new environment
conda create -n ai-prompt-toolkit python=3.9
conda activate ai-prompt-toolkit
conda install -c conda-forge ai-prompt-toolkit
```

### Method 3: From Source

```bash
# Clone the repository
git clone https://github.com/ai-prompt-toolkit/ai-prompt-toolkit.git
cd ai-prompt-toolkit

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[all]"
```

## 🔧 Detailed Installation

### Windows Installation

#### Using Windows Package Manager (winget)

```powershell
# Install Python if not already installed
winget install Python.Python.3.9

# Install AI Prompt Toolkit
pip install ai-prompt-toolkit[all]
```

#### Using Chocolatey

```powershell
# Install Python
choco install python

# Install AI Prompt Toolkit
pip install ai-prompt-toolkit[all]
```

#### Manual Installation

1. **Install Python 3.9+** from [python.org](https://python.org)
2. **Open Command Prompt or PowerShell**
3. **Install the toolkit**:
   ```cmd
   pip install ai-prompt-toolkit[all]
   ```

### macOS Installation

#### Using Homebrew

```bash
# Install Python
brew install python@3.9

# Install AI Prompt Toolkit
pip3 install ai-prompt-toolkit[all]
```

#### Using MacPorts

```bash
# Install Python
sudo port install python39

# Install AI Prompt Toolkit
pip3.9 install ai-prompt-toolkit[all]
```

### Linux Installation

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3.9 python3.9-pip python3.9-venv

# Install AI Prompt Toolkit
pip3 install ai-prompt-toolkit[all]
```

#### CentOS/RHEL/Fedora

```bash
# Install Python
sudo dnf install python3.9 python3-pip

# Install AI Prompt Toolkit
pip3 install ai-prompt-toolkit[all]
```

#### Arch Linux

```bash
# Install Python
sudo pacman -S python python-pip

# Install AI Prompt Toolkit
pip install ai-prompt-toolkit[all]
```

## 🐳 Docker Installation

### Quick Start with Docker

```bash
# Pull the official image
docker pull ai-prompt-toolkit/ai-prompt-toolkit:latest

# Run with default settings
docker run -p 8000:8000 ai-prompt-toolkit/ai-prompt-toolkit:latest

# Run with custom configuration
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://redis:6379 \
  ai-prompt-toolkit/ai-prompt-toolkit:latest
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  ai-prompt-toolkit:
    image: ai-prompt-toolkit/ai-prompt-toolkit:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_prompt_toolkit
      - REDIS_URL=redis://redis:6379
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
      - ollama
    volumes:
      - ./data:/app/data

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_prompt_toolkit
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

Run with:

```bash
docker-compose up -d
```

## 🔧 Configuration Setup

### Environment Variables

Create a `.env` file in your project directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///./ai_prompt_toolkit.db
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_prompt_toolkit

# LLM Provider Configuration
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434

OPENAI_ENABLED=false
OPENAI_API_KEY=your-openai-api-key

ANTHROPIC_ENABLED=false
ANTHROPIC_API_KEY=your-anthropic-api-key

# Security Configuration
SECRET_KEY=your-secret-key-change-in-production
ENABLE_PROMPT_INJECTION_DETECTION=true
ENABLE_GUARDRAILS=true

# Performance Configuration
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=3600

# Monitoring Configuration
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Database Setup

#### SQLite (Default)

No additional setup required. The database file will be created automatically.

#### PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql                         # macOS
sudo dnf install postgresql postgresql-server   # CentOS/RHEL

# Create database
sudo -u postgres createdb ai_prompt_toolkit

# Create user
sudo -u postgres createuser --interactive ai_prompt_toolkit

# Set password
sudo -u postgres psql -c "ALTER USER ai_prompt_toolkit PASSWORD 'your_password';"

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_prompt_toolkit TO ai_prompt_toolkit;"
```

#### MySQL/MariaDB

```bash
# Install MySQL
sudo apt install mysql-server                  # Ubuntu/Debian
brew install mysql                             # macOS
sudo dnf install mysql-server                  # CentOS/RHEL

# Create database and user
mysql -u root -p << EOF
CREATE DATABASE ai_prompt_toolkit;
CREATE USER 'ai_prompt_toolkit'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ai_prompt_toolkit.* TO 'ai_prompt_toolkit'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Redis Setup (Optional)

#### Local Installation

```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# CentOS/RHEL
sudo dnf install redis

# Start Redis
sudo systemctl start redis
# or
redis-server
```

#### Docker Redis

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Ollama Setup (Optional)

#### Install Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download/windows
```

#### Pull Models

```bash
# Pull recommended models
ollama pull llama3.1:latest
ollama pull mistral:latest
ollama pull phi3:mini

# Start Ollama server
ollama serve
```

## 🚀 Initialization

### Initialize the System

```bash
# Initialize database and load default templates
ai-prompt-toolkit init

# Initialize with custom configuration
ai-prompt-toolkit init --config /path/to/config.yaml

# Initialize with specific database
ai-prompt-toolkit init --database-url postgresql://user:pass@host:5432/db
```

### Verify Installation

```bash
# Check system status
ai-prompt-toolkit status

# Run health check
ai-prompt-toolkit health-check

# Test basic functionality
ai-prompt-toolkit test-prompt "Hello, world!"

# Start the server
ai-prompt-toolkit serve
```

### Load Sample Data (Optional)

```bash
# Load sample templates and examples
ai-prompt-toolkit load-samples

# Load specific sample sets
ai-prompt-toolkit load-samples --templates --examples
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Python Version Issues

```bash
# Check Python version
python --version
python3 --version

# Use specific Python version
python3.9 -m pip install ai-prompt-toolkit
```

#### 2. Permission Issues

```bash
# Install for current user only
pip install --user ai-prompt-toolkit

# Use virtual environment
python -m venv ai-prompt-toolkit-env
source ai-prompt-toolkit-env/bin/activate  # Linux/macOS
ai-prompt-toolkit-env\Scripts\activate     # Windows
pip install ai-prompt-toolkit
```

#### 3. Database Connection Issues

```bash
# Test database connection
ai-prompt-toolkit test-db

# Reset database
ai-prompt-toolkit reset-db

# Migrate database
ai-prompt-toolkit migrate
```

#### 4. LLM Provider Issues

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test OpenAI connection
ai-prompt-toolkit test-llm --provider openai

# List available providers
ai-prompt-toolkit providers list
```

#### 5. Port Conflicts

```bash
# Use different port
ai-prompt-toolkit serve --port 8080

# Check what's using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows
```

### Getting Help

If you encounter issues:

1. **Check the logs**:
   ```bash
   ai-prompt-toolkit logs
   ```

2. **Run diagnostics**:
   ```bash
   ai-prompt-toolkit diagnose
   ```

3. **Check system requirements**:
   ```bash
   ai-prompt-toolkit check-requirements
   ```

4. **Get support**:
   - [GitHub Issues](https://github.com/ai-prompt-toolkit/issues)
   - [Discord Community](https://discord.gg/ai-prompt-toolkit)
   - [Documentation](https://docs.ai-prompt-toolkit.com)

## 🎯 Next Steps

After successful installation:

1. **Follow the [Quick Start Guide](quickstart.md)**
2. **Try the [Interactive Tutorial](../examples/notebooks/prompt_optimization_tutorial.ipynb)**
3. **Explore [Examples](examples.md)**
4. **Read [Best Practices](best-practices.md)**
5. **Set up [Monitoring](monitoring.md) for production**

## 📦 Installation Extras

### Available Extras

- `redis`: Redis caching support
- `postgres`: PostgreSQL database support
- `mysql`: MySQL/MariaDB database support
- `monitoring`: Prometheus metrics and monitoring
- `security`: Enhanced security features
- `dev`: Development tools and testing
- `all`: All optional dependencies

### Custom Installation

```bash
# Minimal installation
pip install ai-prompt-toolkit

# With specific features
pip install ai-prompt-toolkit[redis,monitoring]

# Development installation
pip install ai-prompt-toolkit[dev]
git clone https://github.com/ai-prompt-toolkit/ai-prompt-toolkit.git
cd ai-prompt-toolkit
pip install -e ".[dev]"
```

---

**Installation complete!** 🎉 You're ready to start optimizing prompts with the AI Prompt Toolkit.
