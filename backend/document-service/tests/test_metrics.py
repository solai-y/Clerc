"""
Simple test script to verify MetricsAnalyticsService works correctly.
Run this inside the Docker container where dependencies are installed.
"""
import sys
import os

# Add parent directory (app root) to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from services.metrics_analytics import MetricsAnalyticsService

    print("✅ Successfully imported MetricsAnalyticsService")

    # Initialize the service
    service = MetricsAnalyticsService()
    print("✅ Successfully initialized MetricsAnalyticsService")

    # Calculate top-tag accuracy
    result = service.calculate_top_tag_accuracy()
    print("✅ Successfully calculated top-tag accuracy")
    print("\n📊 Results:")
    print(f"   Top-Tag Accuracy: {result['top_tag_accuracy']}%")
    print(f"   Perfect Match Rate: {result['perfect_match_rate']}%")
    print(f"   Primary Accuracy: {result['top_tag_by_level']['primary']}%")
    print(f"   Secondary Accuracy: {result['top_tag_by_level']['secondary']}%")
    print(f"   Tertiary Accuracy: {result['top_tag_by_level']['tertiary']}%")
    print(f"   Total Documents: {result['total_documents']}")
    print(f"   Documents with All Levels: {result['documents_with_all_levels']}")
    print(f"   Perfect Matches: {result['perfect_matches']}")
    print("\n📈 Detailed Metrics:")
    for level, metrics in result['metrics'].items():
        print(f"   {level.capitalize()}: {metrics['accepted']}/{metrics['total']} accepted")

    # Check timing stats presence and validity
    for timing_metric in ['average_timing_s', 'median_timing_s', 'percentile_95_timing_s']:
        timing_value = result.get(timing_metric)
        if timing_value is None:
            print(f"   ⚠️ Warning: {timing_metric} missing from result")
        else:
            print(f"   {timing_metric}: {timing_value}s")
            assert isinstance(timing_value, (int, float)) and timing_value >= 0, f"{timing_metric} invalid"

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
