@echo off
echo Setting up AI Prompt Toolkit environment...

REM Activate the conda environment
call conda activate ai-prompt-toolkit

REM Install core dependencies
echo Installing core dependencies...
pip install fastapi uvicorn langchain langchain-community rich typer structlog

REM Install additional dependencies for the demo
echo Installing additional dependencies...
pip install pydantic pydantic-settings

REM Test Ollama connection
echo Testing Ollama connection...
python -c "print('Testing Ollama...'); from langchain_community.llms import Ollama; print('Ollama imported successfully')"

echo Setup complete!
echo.
echo To run the demo:
echo 1. conda activate ai-prompt-toolkit
echo 2. python scripts\simple_demo.py
pause
