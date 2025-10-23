"""
Simple test script to verify MetricsAnalyticsService works correctly.
Run this inside the Docker container where dependencies are installed.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    print(f"   Overall Accuracy: {result['overall_accuracy']}%")
    print(f"   Primary Accuracy: {result['by_level']['primary']}%")
    print(f"   Secondary Accuracy: {result['by_level']['secondary']}%")
    print(f"   Tertiary Accuracy: {result['by_level']['tertiary']}%")
    print(f"   Total Documents: {result['total_documents']}")
    print("\n📈 Detailed Metrics:")
    for level, metrics in result['metrics'].items():
        print(f"   {level.capitalize()}: {metrics['accepted']}/{metrics['total']} accepted")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
