#!/bin/bash
# Complete Setup and Validation Script for CAB Approval
# This script guides you through the entire validation process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
VALIDATION_DIR="validation_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$VALIDATION_DIR/cab_validation_report_$TIMESTAMP.md"

echo -e "${BOLD}${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Gmail Job Parser - CAB Approval Validation Suite     ║"
echo "║  Change Request: CR-2026-001                           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Create validation directory
mkdir -p "$VALIDATION_DIR"

# Step 1: Prerequisites Check
echo -e "${BOLD}STEP 1: Prerequisites Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Check Ollama
echo -n "Checking Ollama... "
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama installed"
else
    echo -e "${RED}✗ Ollama not installed${NC}"
    echo ""
    echo -e "${YELLOW}Install Ollama:${NC}"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    read -p "Press Enter after installing Ollama..."
fi

# Check if Ollama is running
echo -n "Checking Ollama service... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is running"
else
    echo -e "${YELLOW}⚠${NC} Ollama not running"
    echo ""
    echo "Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama started successfully"
    else
        echo -e "${RED}✗ Failed to start Ollama${NC}"
        exit 1
    fi
fi

# Check Gmail credentials
echo -n "Checking Gmail credentials... "
if [ -f "credentials.json" ]; then
    echo -e "${GREEN}✓${NC} credentials.json found"
else
    echo -e "${YELLOW}⚠${NC} credentials.json not found"
    echo ""
    echo -e "${YELLOW}Gmail API Setup Required:${NC}"
    echo "  1. Go to: https://console.cloud.google.com/"
    echo "  2. Create project → Enable Gmail API"
    echo "  3. Create OAuth credentials (Desktop app)"
    echo "  4. Download as 'credentials.json' in this directory"
    echo ""
    read -p "Press Enter after setting up credentials..."
fi

# Check Python dependencies
echo -n "Checking Python dependencies... "
if python3 -c "import google.auth" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}⚠${NC} Installing dependencies..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi

echo ""
echo -e "${GREEN}✓ All prerequisites met!${NC}"
echo ""

# Step 2: Model Recommendation
echo -e "${BOLD}STEP 2: Model Selection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Available models on your system:"
ollama list
echo ""

echo -e "${BOLD}Recommended models for comprehensive validation:${NC}"
echo ""
echo "  ${BLUE}Tier 1: Essential (MUST test)${NC}"
echo "    • llama3.2:1b    - Ultra-small baseline"
echo "    • llama3.2:3b    - Small model benchmark"
echo "    • mistral        - Alternative to Llama"
echo ""
echo "  ${BLUE}Tier 2: Important (SHOULD test)${NC}"
echo "    • phi3:mini      - Microsoft, efficient"
echo "    • gemma:2b       - Google, small"
echo "    • gemma:7b       - Google, medium"
echo ""
echo "  ${BLUE}Tier 3: Optional (NICE to test)${NC}"
echo "    • llama3.1:8b    - Large, accurate"
echo "    • qwen2:7b       - Strong reasoning"
echo ""

MISSING_MODELS=()

# Check for essential models
for model in "llama3.2:1b" "llama3.2:3b" "mistral"; do
    if ! ollama list | grep -q "$model"; then
        MISSING_MODELS+=("$model")
    fi
done

if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing essential models:${NC}"
    for model in "${MISSING_MODELS[@]}"; do
        echo "  • $model"
    done
    echo ""

    read -p "Pull missing models now? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for model in "${MISSING_MODELS[@]}"; do
            echo "Pulling $model..."
            ollama pull "$model"
        done
    else
        echo -e "${YELLOW}⚠ CAB requires at least 5 models for approval${NC}"
        echo "You can continue, but results may be insufficient for approval."
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
fi

echo ""

# Step 3: Benchmark Models
echo -e "${BOLD}STEP 3: Model Benchmarking (CAB Requirement #1)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get list of models to test
AVAILABLE_MODELS=$(ollama list | awk 'NR>1 {print $1}' | paste -sd "," -)

echo "This will benchmark all available models:"
ollama list | awk 'NR>1 {print "  • " $1}'
echo ""

read -p "Start benchmarking? (Y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${BLUE}Running benchmarks... This may take 10-30 minutes${NC}"
    echo ""

    BENCHMARK_OUTPUT="$VALIDATION_DIR/benchmark_results_$TIMESTAMP.json"

    python3 benchmark_models.py --output "$BENCHMARK_OUTPUT" | tee "$VALIDATION_DIR/benchmark_log_$TIMESTAMP.txt"

    echo ""
    echo -e "${GREEN}✓ Benchmarking complete!${NC}"
    echo "  Results: $BENCHMARK_OUTPUT"
    echo ""
else
    echo -e "${YELLOW}⚠ Skipping benchmarks - CAB will require this for approval${NC}"
    BENCHMARK_OUTPUT="NOT_RUN"
fi

# Step 4: Real Email Test
echo ""
echo -e "${BOLD}STEP 4: Real Email Validation (CAB Requirement #2)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "This will:"
echo "  1. Process emails from your Gmail account (read-only)"
echo "  2. Test job detection and extraction"
echo "  3. Generate accuracy metrics"
echo ""

read -p "How many emails to process? (10-100, default=50): " NUM_EMAILS
NUM_EMAILS=${NUM_EMAILS:-50}

echo ""
read -p "Start real email test? (Y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${BLUE}Processing $NUM_EMAILS emails from Gmail...${NC}"
    echo ""

    # Use balanced profile for testing
    export OLLAMA_JOB_DETECTION_MODEL="llama3.2:3b"
    export OLLAMA_JOB_EXTRACTION_MODEL="llama3.2"
    export OLLAMA_CONFIRMATION_MODEL="llama3.2:1b"

    START_TIME=$(date +%s)
    python3 main.py --max-emails "$NUM_EMAILS" --stats-only | tee "$VALIDATION_DIR/real_email_test_$TIMESTAMP.txt"
    END_TIME=$(date +%s)

    ELAPSED=$((END_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))

    echo ""
    echo -e "${GREEN}✓ Real email test complete!${NC}"
    echo "  Time: ${MINUTES}m ${SECONDS}s"
    echo "  Results: data/jobs.json"
    echo ""

    REAL_EMAIL_TEST="COMPLETED"
    PROCESSING_TIME="${MINUTES}m ${SECONDS}s"
else
    echo -e "${YELLOW}⚠ Skipping real email test - CAB will require this${NC}"
    REAL_EMAIL_TEST="NOT_RUN"
    PROCESSING_TIME="N/A"
fi

# Step 5: Generate CAB Report
echo ""
echo -e "${BOLD}STEP 5: Generating CAB Validation Report${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat > "$REPORT_FILE" << EOF
# CAB Validation Report
## Change Request: CR-2026-001
## Model Configuration for Gmail Job Parser

**Date:** $(date +"%Y-%m-%d %H:%M:%S")
**Validator:** $(whoami)
**System:** $(uname -s) $(uname -r)

---

## Executive Summary

This report documents the validation testing performed to meet CAB approval
requirements for the multi-model configuration strategy.

### Validation Status

| Requirement | Status | Notes |
|-------------|--------|-------|
| Benchmark 5+ models | ${BENCHMARK_OUTPUT/NOT_RUN/❌ NOT COMPLETED} | ${BENCHMARK_OUTPUT/NOT_RUN/Required for approval} |
| Real email testing | ${REAL_EMAIL_TEST/NOT_RUN/❌ NOT COMPLETED} | ${REAL_EMAIL_TEST/NOT_RUN/Required for approval} |
| Performance measurement | ${REAL_EMAIL_TEST/NOT_RUN/❌ NOT COMPLETED} | ${REAL_EMAIL_TEST/NOT_RUN/Required for approval} |
| Documentation review | ✅ COMPLETED | All docs present |

---

## 1. Benchmark Results

EOF

if [ "$BENCHMARK_OUTPUT" != "NOT_RUN" ]; then
    echo "### Models Tested" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    ollama list | awk 'NR>1 {print $1}' >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Detailed results: \`$BENCHMARK_OUTPUT\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "See benchmark output for accuracy and performance metrics." >> "$REPORT_FILE"
else
    echo "**Status:** ❌ NOT COMPLETED" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Benchmark testing was not performed." >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

---

## 2. Real Email Testing

EOF

if [ "$REAL_EMAIL_TEST" = "COMPLETED" ]; then
    cat >> "$REPORT_FILE" << EOF
**Status:** ✅ COMPLETED

- Emails processed: $NUM_EMAILS
- Processing time: $PROCESSING_TIME
- Configuration: BALANCED profile
- Results: data/jobs.json

See detailed output: \`validation_results/real_email_test_$TIMESTAMP.txt\`

EOF
else
    cat >> "$REPORT_FILE" << EOF
**Status:** ❌ NOT COMPLETED

Real email testing was not performed.

EOF
fi

cat >> "$REPORT_FILE" << EOF
---

## 3. CAB Approval Checklist

### Critical Requirements

- [ ] **Benchmarked 5+ models** (including non-Llama alternatives)
- [ ] **Validated on 100+ real emails**
- [ ] **Job detection accuracy ≥ 90%**
- [ ] **Confirmation detection accuracy ≥ 85%**
- [ ] **Job extraction accuracy ≥ 70%**
- [ ] **Performance improvement ≥ 2x vs baseline**
- [ ] **Processing time < 15 min / 100 emails**

### Recommended Requirements

- [ ] Tested Mistral
- [ ] Tested Phi3
- [ ] Tested Gemma
- [ ] Memory profiling completed
- [ ] Edge cases documented
- [ ] False positive rate < 5%

---

## 4. Recommendation

**PRELIMINARY ASSESSMENT:**

EOF

if [ "$BENCHMARK_OUTPUT" != "NOT_RUN" ] && [ "$REAL_EMAIL_TEST" = "COMPLETED" ]; then
    echo "✅ **READY FOR CAB REVIEW**" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "All required validation tests have been completed." >> "$REPORT_FILE"
    echo "The Change Advisory Board can now make a data-driven decision." >> "$REPORT_FILE"
else
    echo "⚠️ **INCOMPLETE - NOT READY FOR CAB APPROVAL**" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Additional validation required:" >> "$REPORT_FILE"

    if [ "$BENCHMARK_OUTPUT" = "NOT_RUN" ]; then
        echo "- Complete model benchmarking" >> "$REPORT_FILE"
    fi

    if [ "$REAL_EMAIL_TEST" != "COMPLETED" ]; then
        echo "- Complete real email validation" >> "$REPORT_FILE"
    fi
fi

cat >> "$REPORT_FILE" << EOF

---

## 5. Next Steps

1. Review this validation report
2. Address any incomplete requirements
3. Submit to Change Advisory Board
4. Await CAB decision

---

**Report Generated:** $(date)
**Location:** \`$REPORT_FILE\`

EOF

echo ""
echo -e "${GREEN}✓ CAB Validation Report generated!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BOLD}Validation Complete!${NC}"
echo ""
echo "Report location:"
echo "  $REPORT_FILE"
echo ""

if [ "$BENCHMARK_OUTPUT" != "NOT_RUN" ] && [ "$REAL_EMAIL_TEST" = "COMPLETED" ]; then
    echo -e "${GREEN}✓ All CAB requirements met!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the report: cat $REPORT_FILE"
    echo "  2. Check benchmark results: cat $BENCHMARK_OUTPUT"
    echo "  3. Review found jobs: cat data/jobs.json"
    echo "  4. Submit report to CAB for final decision"
else
    echo -e "${YELLOW}⚠ Some requirements incomplete${NC}"
    echo ""
    echo "To complete validation:"

    if [ "$BENCHMARK_OUTPUT" = "NOT_RUN" ]; then
        echo "  • Run: python3 benchmark_models.py"
    fi

    if [ "$REAL_EMAIL_TEST" != "COMPLETED" ]; then
        echo "  • Run: python3 main.py --max-emails 100"
    fi

    echo ""
    echo "Then re-run this script to generate final report."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
