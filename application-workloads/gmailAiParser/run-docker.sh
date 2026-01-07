#!/bin/bash
# Easy Docker launcher for Gmail Job Parser with Ollama

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Gmail Job Parser - Docker Launcher"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo -e "${YELLOW}Warning: credentials.json not found${NC}"
    echo "You'll need Gmail API credentials to run the parser"
    echo "See QUICKSTART.md for setup instructions"
    echo ""
fi

# Function to check if Ollama is healthy
check_ollama() {
    docker-compose exec -T ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1
}

# Parse command
case "${1:-run}" in
    "setup"|"init")
        echo "Starting Ollama and initializing models..."
        echo "This may take 5-10 minutes for first run"
        echo ""

        # Start Ollama
        docker-compose up -d ollama

        # Wait for Ollama to be healthy
        echo "Waiting for Ollama to start..."
        sleep 5

        # Initialize models
        docker-compose up ollama-init

        echo ""
        echo -e "${GREEN}✓ Setup complete!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Test models: ./run-docker.sh test"
        echo "  2. Run parser: ./run-docker.sh run"
        ;;

    "test")
        echo "Testing Ollama models..."
        echo ""

        if ! check_ollama; then
            echo -e "${YELLOW}Ollama not running. Starting it first...${NC}"
            docker-compose up -d ollama
            sleep 5
        fi

        docker-compose run --rm job-parser python test_ollama_models.py
        ;;

    "run")
        shift
        MAX_EMAILS="${1:-50}"

        echo "Processing $MAX_EMAILS emails..."
        echo ""

        if ! check_ollama; then
            echo -e "${YELLOW}Ollama not running. Starting it first...${NC}"
            docker-compose up -d ollama
            sleep 5
        fi

        docker-compose run --rm job-parser python main.py --max-emails "$MAX_EMAILS"
        ;;

    "query")
        shift
        QUERY="$*"

        if [ -z "$QUERY" ]; then
            echo "Usage: ./run-docker.sh query 'from:linkedin.com OR from:indeed.com'"
            exit 1
        fi

        echo "Running custom query: $QUERY"
        echo ""

        docker-compose run --rm job-parser python main.py --query "$QUERY"
        ;;

    "list")
        echo "Listing all found jobs..."
        echo ""
        docker-compose run --rm job-parser python main.py --list-jobs
        ;;

    "export")
        shift
        FILENAME="${1:-jobs_export.csv}"

        echo "Exporting jobs to $FILENAME..."
        echo ""
        docker-compose run --rm job-parser python main.py --export "$FILENAME"

        if [ -f "data/$FILENAME" ]; then
            echo -e "${GREEN}✓ Exported to data/$FILENAME${NC}"
        fi
        ;;

    "stats")
        echo "Showing statistics..."
        echo ""
        docker-compose run --rm job-parser python main.py --stats-only
        ;;

    "shell")
        echo "Starting interactive shell..."
        docker-compose run --rm job-parser bash
        ;;

    "logs")
        echo "Showing Ollama logs..."
        docker-compose logs -f ollama
        ;;

    "models")
        echo "Available Ollama models:"
        docker-compose exec ollama ollama list
        ;;

    "pull")
        shift
        MODEL="${1:-llama3.2}"

        echo "Pulling model: $MODEL"
        docker-compose exec ollama ollama pull "$MODEL"
        ;;

    "stop")
        echo "Stopping services..."
        docker-compose down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;

    "restart")
        echo "Restarting services..."
        docker-compose restart
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;

    "clean")
        echo -e "${YELLOW}Warning: This will remove all containers and volumes${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            echo -e "${GREEN}✓ Cleaned up${NC}"
        fi
        ;;

    "help"|"-h"|"--help")
        echo "Usage: ./run-docker.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  setup, init          - Initialize Ollama and download models"
        echo "  test                 - Test Ollama models"
        echo "  run [N]              - Process N emails (default: 50)"
        echo "  query 'QUERY'        - Run custom Gmail query"
        echo "  list                 - List all found jobs"
        echo "  export [FILE]        - Export jobs to CSV"
        echo "  stats                - Show statistics"
        echo "  shell                - Open interactive shell"
        echo "  logs                 - View Ollama logs"
        echo "  models               - List available Ollama models"
        echo "  pull MODEL           - Pull an Ollama model"
        echo "  stop                 - Stop all services"
        echo "  restart              - Restart all services"
        echo "  clean                - Remove all containers and data"
        echo "  help                 - Show this help"
        echo ""
        echo "Examples:"
        echo "  ./run-docker.sh setup"
        echo "  ./run-docker.sh run 100"
        echo "  ./run-docker.sh query 'from:linkedin.com Python developer'"
        echo "  ./run-docker.sh export my_jobs.csv"
        echo "  ./run-docker.sh pull mistral"
        ;;

    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run './run-docker.sh help' for usage"
        exit 1
        ;;
esac
