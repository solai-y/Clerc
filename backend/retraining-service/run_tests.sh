#!/bin/bash

# Retraining Service Test Runner
# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Retraining Service Test Runner${NC}"
echo "======================================"

# Check if test database exists
echo -e "\n${YELLOW}📊 Checking test database...${NC}"
if psql -lqt | cut -d \| -f 1 | grep -qw document_classification_test; then
    echo -e "${GREEN}✓ Test database exists${NC}"
else
    echo -e "${RED}✗ Test database not found${NC}"
    echo -e "${YELLOW}Creating test database...${NC}"
    createdb document_classification_test
    echo -e "${GREEN}✓ Test database created${NC}"
fi

# Run schema migration
echo -e "\n${YELLOW}🗄️  Running database migrations...${NC}"
psql -d document_classification_test -f schema.sql > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${YELLOW}! Migrations may have already been applied${NC}"
fi

# Install test dependencies
echo -e "\n${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q -r tests/requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

# Set environment variables if not already set
export TEST_DB_HOST=${TEST_DB_HOST:-localhost}
export TEST_DB_PORT=${TEST_DB_PORT:-5432}
export TEST_DB_NAME=${TEST_DB_NAME:-document_classification_test}
export TEST_DB_USER=${TEST_DB_USER:-postgres}
export TEST_DB_PASSWORD=${TEST_DB_PASSWORD:-postgres}

echo -e "\n${YELLOW}🔧 Test Configuration:${NC}"
echo "  Host: $TEST_DB_HOST"
echo "  Port: $TEST_DB_PORT"
echo "  Database: $TEST_DB_NAME"
echo "  User: $TEST_DB_USER"

# Parse command line arguments
TEST_TYPE="all"
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=app --cov-report=term-missing --cov-report=html"
            shift
            ;;
        -h|--help)
            echo ""
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --unit           Run unit tests only"
            echo "  --integration    Run integration tests only"
            echo "  -v, --verbose    Verbose output"
            echo "  --coverage       Generate coverage report"
            echo "  -h, --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Run tests
echo -e "\n${YELLOW}🚀 Running tests...${NC}"
echo "======================================"

if [ "$TEST_TYPE" == "unit" ]; then
    echo -e "${YELLOW}Running unit tests only${NC}\n"
    pytest tests/unit/ $VERBOSE $COVERAGE
elif [ "$TEST_TYPE" == "integration" ]; then
    echo -e "${YELLOW}Running integration tests only${NC}\n"
    pytest tests/integration/ $VERBOSE $COVERAGE
else
    echo -e "${YELLOW}Running all tests${NC}\n"
    pytest $VERBOSE $COVERAGE
fi

TEST_EXIT_CODE=$?

# Print results
echo ""
echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"

    if [ -n "$COVERAGE" ]; then
        echo -e "\n${YELLOW}📊 Coverage report generated:${NC}"
        echo "  HTML: htmlcov/index.html"
    fi
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $TEST_EXIT_CODE
