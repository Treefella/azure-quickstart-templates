#!/bin/bash
# Switch between model configuration profiles

set -e

PROFILE="${1:-balanced}"
CONFIG_DIR="configs"
ENV_FILE=".env"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Gmail Job Parser - Profile Switcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate profile
case "$PROFILE" in
    "fast"|"balanced"|"accurate"|"ultrafast")
        CONFIG_FILE="$CONFIG_DIR/${PROFILE}.env"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: ./switch-profile.sh [PROFILE]"
        echo ""
        echo "Available profiles:"
        echo "  ultrafast  - Fastest processing (80-85% accuracy)"
        echo "  fast       - Fast processing (85-90% accuracy)"
        echo "  balanced   - RECOMMENDED (92-95% accuracy) ⭐"
        echo "  accurate   - Best accuracy (95-98%, slower)"
        echo ""
        echo "Examples:"
        echo "  ./switch-profile.sh balanced"
        echo "  ./switch-profile.sh fast"
        echo ""
        echo "See MODEL_STRATEGY.md for detailed comparison"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Unknown profile: $PROFILE${NC}"
        echo "Available: ultrafast, fast, balanced, accurate"
        echo "Run './switch-profile.sh help' for more info"
        exit 1
        ;;
esac

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Error: Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Backup existing .env if present
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    echo -e "${YELLOW}Backed up existing .env to .env.backup${NC}"
fi

# Copy profile config
cp "$CONFIG_FILE" "$ENV_FILE"

echo -e "${GREEN}✓ Switched to '${PROFILE}' profile${NC}"
echo ""

# Show configuration
echo "Configuration:"
echo "--------------------"
grep "^OLLAMA_.*_MODEL=" "$ENV_FILE" | while read line; do
    echo "  $line"
done
echo ""

# Extract models needed
echo "Models required:"
echo "--------------------"
grep "^OLLAMA_.*_MODEL=" "$ENV_FILE" | cut -d'=' -f2 | sort -u | while read model; do
    echo -e "  ${BLUE}$model${NC}"

    # Check if model is pulled (if ollama is available)
    if command -v ollama &> /dev/null; then
        if ollama list | grep -q "^$model"; then
            echo -e "    ${GREEN}✓ Already pulled${NC}"
        else
            echo -e "    ${YELLOW}⚠ Not pulled yet${NC}"
            echo -e "    Run: ${BLUE}ollama pull $model${NC}"
        fi
    fi
done
echo ""

# Show profile info
case "$PROFILE" in
    "ultrafast")
        echo -e "${GREEN}ULTRA-FAST Profile${NC}"
        echo "  Speed: ⚡⚡⚡ Very Fast (~3-5 min / 100 emails)"
        echo "  Accuracy: 80-85%"
        echo "  Model size: 1.3GB total"
        echo "  Best for: Processing thousands of emails"
        ;;
    "fast")
        echo -e "${GREEN}FAST Profile${NC}"
        echo "  Speed: ⚡⚡ Fast (~5-8 min / 100 emails)"
        echo "  Accuracy: 85-90%"
        echo "  Model size: 3.3GB total"
        echo "  Best for: Local CPU, quick results"
        ;;
    "balanced")
        echo -e "${GREEN}BALANCED Profile ⭐ RECOMMENDED${NC}"
        echo "  Speed: ⚡ Medium (~8-12 min / 100 emails)"
        echo "  Accuracy: 92-95%"
        echo "  Model size: 3.3GB total"
        echo "  Best for: Most users, best balance"
        ;;
    "accurate")
        echo -e "${GREEN}ACCURATE Profile${NC}"
        echo "  Speed: Medium-Slow (~15-20 min / 100 emails)"
        echo "  Accuracy: 95-98%"
        echo "  Model size: 6.7GB total"
        echo "  Best for: GPU users, highest quality"
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "Ready to run! Try:"
echo -e "  ${BLUE}python main.py --max-emails 50${NC}"
echo -e "${GREEN}========================================${NC}"
