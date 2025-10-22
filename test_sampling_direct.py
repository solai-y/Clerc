#!/usr/bin/env python3
"""
Direct test of the sampling logic by importing the function
"""
import sys
sys.path.append('backend/ai-service')

# Import the clean_text function directly
from app import clean_text

print("=" * 80)
print("DIRECT SAMPLING LOGIC TEST")
print("Testing the clean_text() function directly")
print("=" * 80)
print()

# Test 1: Short document (should use no sampling)
print("TEST 1: Short document (500 words) - Should use 'none' strategy")
print("-" * 80)
short_text = " ".join(["Short test document."] * 100) + " ENDMARKER"
short_words = len(short_text.split())
print(f"Input: {short_words} words")

result = clean_text(short_text, max_words=5000)
result_words = len(result.split())
print(f"Output: {result_words} words")
print(f"Ratio: {(result_words/short_words)*100:.1f}%")

if "endmarker" in result.lower():
    print("✅ PASS: End marker found (no sampling)")
else:
    print("❌ FAIL: End marker missing")
print()

# Test 2: Medium document (10K words) - Should use weighted sampling
print("TEST 2: Medium document (10,000 words) - Should use 'weighted' strategy")
print("-" * 80)

# Create document with markers
beginning = "BEGINNINGXYZ " + " ".join(["start content"] * 1500)
middle = " MIDDLEXYZ " + " ".join(["middle content"] * 1500)
end = " ENDXYZ " + " ".join(["end content"] * 1500)
medium_text = beginning + middle + end

medium_words = len(medium_text.split())
print(f"Input: {medium_words} words")
print(f"  Beginning marker at word: 0")
print(f"  Middle marker at word: ~3000")
print(f"  End marker at word: ~6000")

result = clean_text(medium_text, max_words=5000)
result_words = len(result.split())
result_lower = result.lower()

print(f"Output: {result_words} words")
print()
print("Markers in output:")
print(f"  BEGINNINGXYZ: {'✓ Found' if 'beginningxyz' in result_lower else '✗ Missing'}")
print(f"  MIDDLEXYZ: {'✓ Found' if 'middlexyz' in result_lower else '✗ Missing'}")
print(f"  ENDXYZ: {'✓ Found' if 'endxyz' in result_lower else '✗ Missing'}")
print()

if 'beginningxyz' in result_lower and 'middlexyz' in result_lower and 'endxyz' in result_lower:
    print("✅ PASS: All sections present (weighted sampling working!)")
elif 'beginningxyz' in result_lower and not 'endxyz' in result_lower:
    print("❌ FAIL: Only beginning found (using first-N, not weighted)")
else:
    print("⚠️  Partial: Check output manually")
print()

# Test 3: Very long document (30K words) - Should use importance sampling
print("TEST 3: Very long document (30,000 words) - Should use 'importance' strategy")
print("-" * 80)

# Create document with high-value sentence in middle
filler = " ".join(["generic filler text"] * 5000)  # 15K words
high_value = " IMPORTANTXYZ company announced revenue of fifty billion dollars with earnings growth profit margin "
very_long_text = filler + high_value + filler

very_long_words = len(very_long_text.split())
print(f"Input: {very_long_words} words")
print(f"High-value sentence position: ~{len(filler.split())} words")

result = clean_text(very_long_text, max_words=5000)
result_words = len(result.split())
result_lower = result.lower()

print(f"Output: {result_words} words")
print()
print("High-value content in output:")
print(f"  IMPORTANTXYZ: {'✓ Found' if 'importantxyz' in result_lower else '✗ Missing'}")
print(f"  'revenue': {'✓ Found' if 'revenue' in result_lower else '✗ Missing'}")
print(f"  'earnings': {'✓ Found' if 'earnings' in result_lower else '✗ Missing'}")
print(f"  'profit': {'✓ Found' if 'profit' in result_lower else '✗ Missing'}")
print()

keyword_count = sum([
    'importantxyz' in result_lower,
    'revenue' in result_lower,
    'earnings' in result_lower,
    'profit' in result_lower
])

if keyword_count >= 3:
    print(f"✅ PASS: Found {keyword_count}/4 keywords (importance sampling working!)")
elif keyword_count == 0:
    print("❌ FAIL: No keywords found (using first-N only)")
else:
    print(f"⚠️  Partial: Found {keyword_count}/4 keywords")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("This test directly calls clean_text() to prove:")
print("1. Short docs: No sampling (full document)")
print("2. Medium docs (5-20K): Weighted sampling (beginning/middle/end)")
print("3. Long docs (>20K): Importance sampling (keyword-based)")
print()
print("Look for the console output above showing which strategy was used!")
print("=" * 80)
