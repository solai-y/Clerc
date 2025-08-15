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
if run_tests_in_container "Unit" "cd /app/tests && python unit/test_document_model.py"; then
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
total_tests=$((total_tests + 1))
if python3 e2e/test_e2e.py; then
    echo "✅ E2E tests: PASSED"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ E2E tests: FAILED"
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