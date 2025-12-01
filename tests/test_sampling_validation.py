#!/usr/bin/env python3
"""
Test to PROVE that dynamic sampling is actually working correctly.
This validates that we're not just taking first N words blindly.
"""
import time
import requests
import json

AI_SERVICE_URL = "http://localhost:5004"

print("=" * 80)
print("DYNAMIC SAMPLING VALIDATION TEST")
print("Proving that different strategies are actually being used")
print("=" * 80)
print()

# ==============================================================================
# TEST 1: Weighted Sampling - Verify middle and end content is captured
# ==============================================================================
print("\nTEST 1: Weighted Sampling (10,000 words)")
print("-" * 80)
print("Expected: 70% beginning, 20% middle, 10% end")
print()

# Create a document with UNIQUE markers in different sections
beginning_marker = "BEGINNING_SECTION_MARKER_UNIQUE_12345"
middle_marker = "MIDDLE_SECTION_MARKER_UNIQUE_67890"
end_marker = "END_SECTION_MARKER_UNIQUE_ABCDE"

# Build 10,000 word document
beginning_filler = " ".join(["Apple Inc reported earnings."] * 1200)  # ~6000 words
middle_filler = " ".join(["The company showed revenue growth."] * 600)  # ~3000 words
end_filler = " ".join(["Management provided forward guidance."] * 200)  # ~1000 words

test_doc_weighted = (
    f"{beginning_marker} {beginning_filler} " +
    f"{middle_marker} {middle_filler} " +
    f"{end_marker} {end_filler}"
)

word_count = len(test_doc_weighted.split())
print(f"Document length: {word_count:,} words")

response = requests.post(
    f"{AI_SERVICE_URL}/predict",
    json={"text": test_doc_weighted},
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    processed_text = result.get("processed_text", "")
    processed_lower = processed_text.lower()

    # Check if markers are present
    has_beginning = beginning_marker.lower() in processed_lower
    has_middle = middle_marker.lower() in processed_lower
    has_end = end_marker.lower() in processed_lower

    print(f"✓ Request successful")
    print(f"  Processed: {len(processed_text.split()):,} words")
    print()
    print("Marker Presence (proves sampling strategy):")
    print(f"  BEGINNING marker found: {'✓ YES' if has_beginning else '✗ NO'}")
    print(f"  MIDDLE marker found:    {'✓ YES' if has_middle else '✗ NO'}")
    print(f"  END marker found:       {'✓ YES' if has_end else '✗ NO'}")
    print()

    if has_beginning and has_middle and has_end:
        print("✅ PASS: Weighted sampling is working correctly!")
        print("   All three sections (beginning/middle/end) are present.")
    else:
        print("❌ FAIL: Not using weighted sampling!")
        print("   Missing sections - likely just taking first N words.")
else:
    print(f"✗ Request failed: {response.status_code}")

# ==============================================================================
# TEST 2: Importance Sampling - Verify keyword-rich sentences are selected
# ==============================================================================
print("\n" + "=" * 80)
print("\nTEST 2: Importance Sampling (25,000 words)")
print("-" * 80)
print("Expected: Sentences with financial keywords should be prioritized")
print()

# Create document with HIGH-VALUE sentence buried in the middle
# and LOW-VALUE filler everywhere else

high_value_sentence = (
    "UNIQUEKEYWORD Apple Inc announced quarterly revenue of $50.2 billion, "
    "representing 15% year-over-year growth with earnings per share of $1.52, "
    "beating analyst expectations and showing strong profit margins across all segments."
)

low_value_filler = "This is generic text with no financial information or relevance. "

# Build 25,000 word document
# Put high-value sentence at position 12,500 (exact middle)
first_half = " ".join([low_value_filler] * 1250)  # ~12,500 words
second_half = " ".join([low_value_filler] * 1250)  # ~12,500 words

test_doc_importance = f"{first_half} {high_value_sentence} {second_half}"

word_count = len(test_doc_importance.split())
print(f"Document length: {word_count:,} words")
print(f"High-value sentence position: ~{len(first_half.split()):,} words in")
print(f"Contains keywords: revenue, earnings, growth, profit, analyst")
print()

response = requests.post(
    f"{AI_SERVICE_URL}/predict",
    json={"text": test_doc_importance},
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    processed_text = result.get("processed_text", "")
    processed_lower = processed_text.lower()

    # Check if high-value sentence is captured
    has_unique_keyword = "uniquekeyword" in processed_lower
    has_revenue = "revenue" in processed_lower
    has_earnings = "earnings" in processed_lower

    print(f"✓ Request successful")
    print(f"  Processed: {len(processed_text.split()):,} words")
    print()
    print("Keyword Presence (proves importance sampling):")
    print(f"  UNIQUEKEYWORD found: {'✓ YES' if has_unique_keyword else '✗ NO'}")
    print(f"  'revenue' found:     {'✓ YES' if has_revenue else '✗ NO'}")
    print(f"  'earnings' found:    {'✓ YES' if has_earnings else '✗ NO'}")
    print()

    if has_unique_keyword and has_revenue and has_earnings:
        print("✅ PASS: Importance sampling is working correctly!")
        print("   High-value sentence from middle of document was selected.")
    else:
        print("❌ FAIL: Not using importance sampling!")
        print("   If just taking first 5K words, wouldn't find middle content.")
else:
    print(f"✗ Request failed: {response.status_code}")

# ==============================================================================
# TEST 3: No Sampling - Verify full document is used for short docs
# ==============================================================================
print("\n" + "=" * 80)
print("\nTEST 3: No Sampling (500 words)")
print("-" * 80)
print("Expected: Full document should be processed (no sampling)")
print()

# Create 500 word document with unique marker at the very end
test_doc_short = " ".join(["Short document test."] * 90)  # ~450 words
unique_end_marker = " FINAL_WORD_MARKER_ZZZZ"
test_doc_short += unique_end_marker

word_count = len(test_doc_short.split())
print(f"Document length: {word_count:,} words")
print(f"Unique marker at position: {word_count} (last word)")
print()

response = requests.post(
    f"{AI_SERVICE_URL}/predict",
    json={"text": test_doc_short},
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    processed_text = result.get("processed_text", "")
    processed_lower = processed_text.lower()
    processed_words = len(processed_text.split())

    has_marker = "marker" in processed_lower and "zzzz" in processed_lower

    print(f"✓ Request successful")
    print(f"  Original: {word_count:,} words")
    print(f"  Processed: {processed_words:,} words")
    print()
    print("Verification:")
    print(f"  End marker found: {'✓ YES' if has_marker else '✗ NO'}")
    print()

    # For short docs, processed count should be close to original
    # (might be slightly less due to stop word removal)
    retention_rate = (processed_words / word_count) * 100

    if has_marker and retention_rate > 70:
        print(f"✅ PASS: No sampling (full document used)")
        print(f"   Retention: {retention_rate:.1f}% of words after stop-word removal")
    else:
        print(f"❌ FAIL: Sampling was applied to short document!")
        print(f"   Retention: {retention_rate:.1f}% (should be >70%)")
else:
    print(f"✗ Request failed: {response.status_code}")

# ==============================================================================
# TEST 4: Compare first-N vs weighted sampling directly
# ==============================================================================
print("\n" + "=" * 80)
print("\nTEST 4: Direct Comparison - First-N vs Weighted Sampling")
print("-" * 80)
print("Create document where weighted sampling would behave differently")
print()

# Create 10K word doc with:
# - Boring content at start
# - Important content in middle
# - Critical conclusion at end

boring_start = " ".join(["This is preliminary background information."] * 1000)  # ~5000 words
important_middle = "MIDDLE_CRITICAL_INFO The company announced a major merger worth $10 billion."
critical_end = "CONCLUSION_CRITICAL_INFO Management confirmed the acquisition will close in Q3."
boring_end = " ".join(["Additional details are provided below."] * 800)  # ~4000 words

test_doc_comparison = f"{boring_start} {important_middle} {boring_end} {critical_end}"

word_count = len(test_doc_comparison.split())
print(f"Document length: {word_count:,} words")
print()
print("Document structure:")
print("  - Words 0-5,000: Boring preliminary info")
print("  - Word ~5,001: MIDDLE_CRITICAL_INFO (merger announcement)")
print("  - Word ~9,000: CONCLUSION_CRITICAL_INFO (acquisition close date)")
print()

response = requests.post(
    f"{AI_SERVICE_URL}/predict",
    json={"text": test_doc_comparison},
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    processed_text = result.get("processed_text", "")
    processed_lower = processed_text.lower()

    has_middle = "middle" in processed_lower and "critical" in processed_lower
    has_conclusion = "conclusion" in processed_lower
    has_merger = "merger" in processed_lower
    has_acquisition = "acquisition" in processed_lower

    print(f"✓ Request successful")
    print(f"  Processed: {len(processed_text.split()):,} words")
    print()
    print("Content Analysis:")
    print(f"  MIDDLE section found:      {'✓ YES' if has_middle else '✗ NO'}")
    print(f"  CONCLUSION section found:  {'✓ YES' if has_conclusion else '✗ NO'}")
    print(f"  'merger' keyword found:    {'✓ YES' if has_merger else '✗ NO'}")
    print(f"  'acquisition' found:       {'✓ YES' if has_acquisition else '✗ NO'}")
    print()

    if has_middle or has_conclusion:
        print("✅ PASS: Using weighted sampling (not just first-N)!")
        print("   Found content from middle/end sections.")
        if has_merger and has_acquisition:
            print("   Bonus: Both key business terms captured!")
    else:
        print("❌ FAIL: Appears to be using first-N sampling only!")
        print("   Would have found middle/end content with weighted sampling.")
else:
    print(f"✗ Request failed: {response.status_code}")

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()
print("This test proves dynamic sampling is working by:")
print()
print("1. TEST 1: Verifying weighted sampling captures beginning/middle/end")
print("   (Not just first 5000 words)")
print()
print("2. TEST 2: Verifying importance sampling finds keyword-rich content")
print("   (From middle of 25K word document)")
print()
print("3. TEST 3: Verifying short documents are fully processed")
print("   (No sampling applied when unnecessary)")
print()
print("4. TEST 4: Directly comparing first-N vs weighted behavior")
print("   (Weighted finds content beyond first 5K words)")
print()
print("If all tests pass, the dynamic sampling strategy is provably working!")
print("=" * 80)
