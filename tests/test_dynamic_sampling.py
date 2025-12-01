#!/usr/bin/env python3
"""
Test dynamic sampling strategy with different document lengths
"""
import time
import requests
import json

# Test cases with different lengths to trigger different strategies
test_cases = [
    {
        "name": "Short (should use: none)",
        "words": 500,
        "expected_strategy": "none",
        "text": " ".join(["Apple Inc announced earnings today."] * 50)  # ~500 words
    },
    {
        "name": "Medium (should use: none)",
        "words": 4000,
        "expected_strategy": "none",
        "text": " ".join(["The company reported strong quarterly revenue growth."] * 500)  # ~4000 words
    },
    {
        "name": "Long (should use: weighted)",
        "words": 10000,
        "expected_strategy": "weighted",
        "text": " ".join(["Apple Inc reported quarterly financial results showing growth."] * 1250)  # ~10000 words
    },
    {
        "name": "Very Long (should use: importance)",
        "words": 25000,
        "expected_strategy": "importance",
        "text": " ".join(["The corporation announced revenue of $50 billion in Q4 2024."] * 2500)  # ~25000 words
    },
    {
        "name": "Extreme (should use: importance)",
        "words": 50000,
        "expected_strategy": "importance",
        "text": " ".join(["Company XYZ Inc disclosed annual earnings showing 15% growth year over year."] * 4000)  # ~50000 words
    }
]

AI_SERVICE_URL = "http://localhost:5004"

print("=" * 80)
print("DYNAMIC SAMPLING STRATEGY TEST")
print("=" * 80)
print()

results = []

for test in test_cases:
    text = test["text"]
    actual_words = len(text.split())

    print(f"\n{test['name']}")
    print(f"  Expected strategy: {test['expected_strategy']}")
    print(f"  Document length: {actual_words:,} words")
    print("-" * 80)

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
            service_elapsed = result.get("elapsed_seconds", 0)
            processed_text = result.get("processed_text", "")
            processed_words = len(processed_text.split())

            print(f"  ✓ Success")
            print(f"  Total time: {total_duration:.3f}s")
            print(f"  Service time: {service_elapsed:.3f}s")
            print(f"  Processed words: {processed_words:,} (from {actual_words:,})")

            # Check predictions
            prediction = result.get("prediction", {})
            if prediction:
                print(f"  Predictions:")
                for level in ["primary", "secondary", "tertiary"]:
                    if level in prediction and prediction[level]:
                        level_data = prediction[level]
                        if isinstance(level_data, dict):
                            print(f"    {level}: {level_data.get('pred', 'N/A')} ({level_data.get('confidence', 0):.2%})")

            results.append({
                "name": test["name"],
                "expected_strategy": test["expected_strategy"],
                "words": actual_words,
                "time": total_duration,
                "processed_words": processed_words,
                "success": True
            })

        else:
            print(f"  ✗ Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            results.append({
                "name": test["name"],
                "expected_strategy": test["expected_strategy"],
                "words": actual_words,
                "success": False,
                "error": response.status_code
            })

    except requests.exceptions.Timeout:
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"  ✗ Timeout after {total_duration:.3f}s")
        results.append({
            "name": test["name"],
            "expected_strategy": test["expected_strategy"],
            "words": actual_words,
            "success": False,
            "error": "timeout"
        })

    except Exception as e:
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"  ✗ Error after {total_duration:.3f}s: {str(e)}")
        results.append({
            "name": test["name"],
            "expected_strategy": test["expected_strategy"],
            "words": actual_words,
            "success": False,
            "error": str(e)
        })

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print(f"{'Test Case':<30} {'Words':<10} {'Strategy':<12} {'Time':<8} {'Status':<10}")
print("-" * 80)

for r in results:
    status = "✓ Pass" if r.get("success") else "✗ Fail"
    time_str = f"{r.get('time', 0):.2f}s" if r.get("success") else "N/A"
    print(f"{r['name']:<30} {r['words']:<10,} {r['expected_strategy']:<12} {time_str:<8} {status:<10}")

print()
print("=" * 80)
print("PERFORMANCE ANALYSIS")
print("=" * 80)
print()

successful = [r for r in results if r.get("success")]
if successful:
    print(f"Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.0f}%)")
    print()
    print(f"{'Document Size':<20} {'Avg Time':<15} {'Speedup vs Baseline':<25}")
    print("-" * 60)

    baseline_time = 60  # Previous timeout threshold

    for r in successful:
        speedup = baseline_time / r['time'] if r['time'] > 0 else 0
        print(f"{r['words']:>6,} words{'':<8} {r['time']:>6.2f}s{'':<8} {speedup:>6.1f}x faster")
else:
    print("No successful tests to analyze")

print()
print("Test Complete!")
