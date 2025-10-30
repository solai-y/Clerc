#!/usr/bin/env python3
"""
Test AI service response time directly
"""
import time
import requests
import json

# Test with various text lengths
test_cases = [
    {
        "name": "Short text",
        "text": "Apple Inc. announced today that Tim Cook will step down as CEO."
    },
    {
        "name": "Medium text",
        "text": " ".join(["This is a test sentence about business and technology."] * 20)
    },
    {
        "name": "Long text",
        "text": " ".join(["This is a test sentence about business operations, financial reporting, technology innovations, and corporate governance."] * 100)
    },
    {
        "name": "Very long text",
        "text": " ".join(["The company announced quarterly earnings showing strong growth in revenue and profitability across all business segments including technology, operations, and services."] * 200)
    }
]

AI_SERVICE_URL = "http://localhost:5004"

print("Testing AI Service Response Times")
print("=" * 80)

for test in test_cases:
    text = test["text"]
    text_length = len(text)
    word_count = len(text.split())

    print(f"\n{test['name']}: {text_length} chars, {word_count} words")
    print("-" * 80)

    # Make the request
    start_time = time.time()

    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/predict",
            json={"text": text},
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        end_time = time.time()
        total_duration = end_time - start_time

        if response.status_code == 200:
            result = response.json()

            # Get the elapsed time from the service itself
            service_elapsed = result.get("elapsed_seconds", 0)

            print(f"✓ Success")
            print(f"  - Total request time: {total_duration:.3f}s")
            print(f"  - AI model time (from service): {service_elapsed:.3f}s")
            print(f"  - Network/overhead: {(total_duration - service_elapsed):.3f}s")

            # Show predictions
            prediction = result.get("prediction", {})
            if prediction:
                print(f"  - Predictions:")
                for level in ["primary", "secondary", "tertiary"]:
                    if level in prediction:
                        level_data = prediction[level]
                        if isinstance(level_data, dict):
                            print(f"    {level}: {level_data.get('pred', 'N/A')} ({level_data.get('confidence', 0):.2%})")
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(f"  - Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"✗ Timeout after {total_duration:.3f}s")

    except Exception as e:
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"✗ Error after {total_duration:.3f}s: {str(e)}")

print("\n" + "=" * 80)
print("Test Complete")
