#!/bin/bash

echo "=================================================="
echo "DOCUMENT SERVICE CONTAINER-BASED TESTS"
echo "=================================================="

# Function to run tests in container
run_tests_in_container() {
    local test_type=$1
    local test_command=$2
    
    echo ""
    echo "🧪 Running $test_type tests in container..."
    echo "Command: $test_command"
    echo "--------------------------------------------------"
    
    docker exec backend-document-service-1 bash -c "$test_command"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ $test_type tests: PASSED"
    else
        echo "❌ $test_type tests: FAILED"
    fi
    
    return $exit_code
}

# Check if container is running
if ! docker ps | grep -q backend-document-service-1; then
    echo "❌ Document service container is not running!"
    echo "Please start it with: docker-compose up -d document-service"
    exit 1
fi

echo "✅ Document service container is running"

# Initialize counters
total_tests=0
passed_tests=0

# Run unit tests
total_tests=$((total_tests + 1))
if run_tests_in_container "Unit" "cd /app/tests && python -m pytest unit/ -v"; then
    passed_tests=$((passed_tests + 1))
fi

# Run integration tests
total_tests=$((total_tests + 1))
if run_tests_in_container "Integration" "cd /app/tests && python -m pytest integration/ -v"; then
    passed_tests=$((passed_tests + 1))
fi

# Run E2E tests from outside container (they connect via HTTP)
echo ""
echo "🌐 Running E2E tests from host..."
echo "--------------------------------------------------"
cd tests

# Check if pytest is available in host system
if ! command -v python3 &> /dev/null || ! python3 -c "import pytest" &> /dev/null; then
    echo "⚠️  pytest not available on host system"
    echo "Running E2E tests individually with python3..."
    
    total_tests=$((total_tests + 5))  # 5 E2E test files
    e2e_passed=0
    
    for test_file in e2e/*.py; do
        if [ -f "$test_file" ]; then
            echo "Running $test_file..."
            if python3 "$test_file"; then
                echo "✅ $(basename $test_file): PASSED"
                e2e_passed=$((e2e_passed + 1))
            else
                echo "❌ $(basename $test_file): FAILED"
            fi
        fi
    done
    
    passed_tests=$((passed_tests + e2e_passed))
    echo "E2E Results: $e2e_passed/5 tests passed"
else
    total_tests=$((total_tests + 1))
    if python3 -m pytest e2e/ -v; then
        echo "✅ E2E tests: PASSED"
        passed_tests=$((passed_tests + 1))
    else
        echo "❌ E2E tests: FAILED"
    fi
fi

echo ""
echo "=================================================="
echo "FINAL TEST RESULTS"
echo "=================================================="
echo "✅ Passed: $passed_tests/$total_tests"
echo "❌ Failed: $((total_tests - passed_tests))/$total_tests"

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 ALL TESTS PASSED!"
    exit 0
else
    echo "💥 SOME TESTS FAILED!"
    exit 1
fi