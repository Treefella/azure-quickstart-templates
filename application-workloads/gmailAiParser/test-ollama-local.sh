#!/bin/bash
# Quick Ollama Test Script - Run this on your local machine
# Tests Ollama connection and runs basic job parsing validation

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Ollama Job Parser - Quick Test"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Ollama Connection
echo "TEST 1: Checking Ollama Connection"
echo "────────────────────────────────────────────────────────────"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
    echo ""
    echo "Available models:"
    curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep '"name"' | head -10
    echo ""
else
    echo -e "${RED}✗ Ollama not accessible at localhost:11434${NC}"
    echo ""
    echo "Start Ollama with: ollama serve"
    exit 1
fi

# Test 2: Check Required Models
echo ""
echo "TEST 2: Checking Required Models"
echo "────────────────────────────────────────────────────────────"

REQUIRED_MODELS=("llama3.2:1b" "llama3.2:3b" "mistral")
MISSING_MODELS=()

for model in "${REQUIRED_MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo -e "${GREEN}✓${NC} $model"
    else
        echo -e "${YELLOW}⚠${NC} $model (missing)"
        MISSING_MODELS+=("$model")
    fi
done

if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Missing models detected. Pull them with:${NC}"
    for model in "${MISSING_MODELS[@]}"; do
        echo "  ollama pull $model"
    done
    echo ""
    read -p "Pull missing models now? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for model in "${MISSING_MODELS[@]}"; do
            echo "Pulling $model..."
            ollama pull "$model"
        done
    fi
fi

# Test 3: Simple AI Test
echo ""
echo "TEST 3: Testing AI Response"
echo "────────────────────────────────────────────────────────────"

TEST_MODEL="llama3.2:3b"
if ollama list | grep -q "$TEST_MODEL"; then
    echo "Sending test prompt to $TEST_MODEL..."

    RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{
      "model": "'$TEST_MODEL'",
      "prompt": "Is this a job email? Subject: Senior Windows Engineer - Remote - £450/day. Answer YES or NO only.",
      "stream": false
    }' | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])")

    echo "Response: $RESPONSE"

    if [[ "$RESPONSE" == *"YES"* ]] || [[ "$RESPONSE" == *"yes"* ]]; then
        echo -e "${GREEN}✓ AI responding correctly${NC}"
    else
        echo -e "${YELLOW}⚠ Unexpected response${NC}"
    fi
else
    echo -e "${YELLOW}⚠ $TEST_MODEL not available, skipping AI test${NC}"
fi

# Test 4: Python Environment
echo ""
echo "TEST 4: Checking Python Environment"
echo "────────────────────────────────────────────────────────────"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"

    # Check if requests is installed
    if python3 -c "import requests" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} requests library installed"
    else
        echo -e "${YELLOW}⚠${NC} requests library missing"
        echo "Install with: pip install requests"
    fi
else
    echo -e "${RED}✗ Python 3 not found${NC}"
fi

# Test 5: Quick Job Email Test
echo ""
echo "TEST 5: Testing Job Email Detection"
echo "────────────────────────────────────────────────────────────"

cat > /tmp/test_job_detection.py << 'PYTHON_SCRIPT'
import requests
import json
import sys

OLLAMA_URL = "http://localhost:11434/api/generate"

def test_job_detection(subject, body, expected):
    """Test if Ollama can detect job emails"""

    prompt = f"""Is this a job opportunity email? Answer with only YES or NO.

Subject: {subject}
Body: {body[:200]}

Answer:"""

    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        answer = result['response'].strip().upper()

        is_job = 'YES' in answer
        correct = is_job == expected

        status = "✓" if correct else "✗"
        print(f"  {status} Subject: {subject[:50]}...")
        print(f"    Expected: {'YES' if expected else 'NO'}, Got: {answer[:20]}, Correct: {correct}")

        return correct
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

# Test cases
test_cases = [
    ("Senior SCCM Engineer - £500/day", "We need an SCCM engineer for Windows deployment...", True),
    ("Your Amazon Order Shipped", "Your package is on the way...", False),
    ("Windows 11 Deployment Specialist", "Seeking specialist for Intune and Autopilot...", True),
]

print("Testing job detection accuracy...")
results = []
for subject, body, expected in test_cases:
    results.append(test_job_detection(subject, body, expected))

accuracy = sum(results) / len(results) * 100
print(f"\nAccuracy: {accuracy:.0f}% ({sum(results)}/{len(results)} correct)")

if accuracy >= 66:
    print("✓ Job detection working!")
    sys.exit(0)
else:
    print("⚠ Job detection needs improvement")
    sys.exit(1)
PYTHON_SCRIPT

if python3 /tmp/test_job_detection.py 2>&1; then
    echo -e "${GREEN}✓ Job detection test passed${NC}"
else
    echo -e "${YELLOW}⚠ Job detection test had issues${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Test Summary"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Ollama is ready for job parsing!"
echo ""
echo "Next steps:"
echo "  1. Run full benchmark: python benchmark_models.py"
echo "  2. Process Gmail: python main.py --max-emails 50"
echo "  3. Launch GUI: python job_parser_gui.py"
echo ""
echo "════════════════════════════════════════════════════════════"
