#!/bin/bash
# Setup script for Gmail Job Parser

set -e

echo "=========================================="
echo "Gmail Job Parser - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || {
    echo "Error: Python 3 is not installed"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create data directory
echo "Creating data directory..."
mkdir -p data
echo "✓ Data directory created"

# Check for credentials.json
echo ""
echo "Checking for Gmail API credentials..."
if [ ! -f "credentials.json" ]; then
    echo "⚠ WARNING: credentials.json not found"
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing one"
    echo "3. Enable Gmail API"
    echo "4. Create OAuth 2.0 credentials (Desktop application)"
    echo "5. Download credentials and save as 'credentials.json' in this directory"
    echo ""
else
    echo "✓ credentials.json found"
fi

# Check if Ollama is running
echo ""
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"

    # Check for required models
    echo "Checking for required models..."
    if ollama list | grep -q "llama3.2"; then
        echo "✓ llama3.2 model found"
    else
        echo "⚠ llama3.2 model not found"
        echo "Run: ollama pull llama3.2"
    fi
else
    echo "⚠ WARNING: Ollama is not running"
    echo ""
    echo "Please install and start Ollama:"
    echo "1. Install from https://ollama.ai"
    echo "2. Run: ollama serve"
    echo "3. Pull model: ollama pull llama3.2"
    echo ""
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure credentials.json is in place"
echo "2. Start Ollama: ollama serve"
echo "3. Pull model: ollama pull llama3.2"
echo "4. Run the parser: python main.py --max-emails 10"
echo ""
echo "For help: python main.py --help"
echo ""
