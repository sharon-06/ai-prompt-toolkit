#!/usr/bin/env python3
"""
Setup script for AI Prompt Toolkit.
This script helps users set up the environment and get started quickly.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result.returncode == 0


def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    print("✅ Python version OK")
    
    # Check Poetry
    if not shutil.which("poetry"):
        print("❌ Poetry is not installed. Please install it first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        return False
    print("✅ Poetry found")
    
    # Check Ollama (optional)
    if shutil.which("ollama"):
        print("✅ Ollama found")
    else:
        print("⚠️  Ollama not found (optional for local LLM support)")
    
    return True


def setup_environment():
    """Set up the development environment."""
    print("\n🛠  Setting up environment...")
    
    # Install dependencies
    if not run_command("poetry install"):
        print("❌ Failed to install dependencies")
        return False
    print("✅ Dependencies installed")
    
    # Copy environment file
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Environment file created (.env)")
        print("   Please edit .env with your configuration")
    
    return True


def initialize_database():
    """Initialize the database and load templates."""
    print("\n💾 Initializing database...")
    
    if not run_command("poetry run ai-prompt-toolkit init"):
        print("❌ Failed to initialize database")
        return False
    
    print("✅ Database initialized with built-in templates")
    return True


def setup_ollama():
    """Set up Ollama if available."""
    if not shutil.which("ollama"):
        print("\n⚠️  Ollama not found. Skipping Ollama setup.")
        print("   To install Ollama: https://ollama.ai/download")
        return True
    
    print("\n🦙 Setting up Ollama...")
    
    # Check if Ollama is running
    if not run_command("ollama list", check=False):
        print("⚠️  Ollama service not running. Please start it:")
        print("   ollama serve")
        return True
    
    # Pull the default model
    print("📥 Pulling llama3.1:latest model (this may take a while)...")
    if run_command("ollama pull llama3.1:latest", check=False):
        print("✅ Ollama model ready")
    else:
        print("⚠️  Failed to pull model. You can do this manually later:")
        print("   ollama pull llama3.1:latest")
    
    return True


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")
    
    if not run_command("poetry run pytest tests/ -v"):
        print("❌ Some tests failed")
        return False
    
    print("✅ All tests passed")
    return True


def main():
    """Main setup function."""
    print("🚀 AI Prompt Toolkit Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required tools.")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("\n❌ Database initialization failed")
        sys.exit(1)
    
    # Setup Ollama
    setup_ollama()
    
    # Run tests
    if "--skip-tests" not in sys.argv:
        if not run_tests():
            print("\n⚠️  Tests failed, but setup is complete")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys (if using external providers)")
    print("2. Start the server: poetry run ai-prompt-toolkit serve")
    print("3. Open http://localhost:8000/docs for API documentation")
    print("4. Try the CLI: poetry run ai-prompt-toolkit --help")
    
    print("\nUseful commands:")
    print("- poetry run ai-prompt-toolkit status    # Check system status")
    print("- poetry run ai-prompt-toolkit serve     # Start the server")
    print("- poetry run pytest                      # Run tests")
    print("- poetry run ai-prompt-toolkit --help    # CLI help")


if __name__ == "__main__":
    main()
