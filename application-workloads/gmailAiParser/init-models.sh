#!/bin/bash
# Initialize Ollama models for Gmail Job Parser

set -e

echo "=========================================="
echo "Initializing Ollama Models"
echo "=========================================="
echo ""

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama..."
    sleep 2
done
echo "✓ Ollama is ready"
echo ""

# Get model names from environment or use defaults
JOB_DETECTION_MODEL="${OLLAMA_JOB_DETECTION_MODEL:-llama3.2}"
JOB_EXTRACTION_MODEL="${OLLAMA_JOB_EXTRACTION_MODEL:-llama3.2}"
CONFIRMATION_MODEL="${OLLAMA_CONFIRMATION_MODEL:-llama3.2}"

# Collect unique models
MODELS=("$JOB_DETECTION_MODEL" "$JOB_EXTRACTION_MODEL" "$CONFIRMATION_MODEL")
UNIQUE_MODELS=($(printf "%s\n" "${MODELS[@]}" | sort -u))

echo "Models to initialize:"
for model in "${UNIQUE_MODELS[@]}"; do
    echo "  - $model"
done
echo ""

# Pull each unique model
for model in "${UNIQUE_MODELS[@]}"; do
    echo "Pulling model: $model"
    echo "------------------------------------------"

    if curl -s -X POST http://ollama:11434/api/pull \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model\"}" | grep -q "success"; then
        echo "✓ Successfully pulled $model"
    else
        # Try using ollama CLI
        OLLAMA_HOST=http://ollama:11434 ollama pull "$model"
        echo "✓ Successfully pulled $model"
    fi
    echo ""
done

echo "=========================================="
echo "Model Initialization Complete!"
echo "=========================================="
echo ""
echo "Available models:"
curl -s http://ollama:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "Could not list models"
echo ""
