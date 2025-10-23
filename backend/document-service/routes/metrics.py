import logging
from fastapi import APIRouter, HTTPException
from models.response import APIResponse
from services.metrics_analytics import MetricsAnalyticsService

logger = logging.getLogger(__name__)

# Initialize router
metrics_router = APIRouter()

# Initialize metrics service
try:
    metrics_service = MetricsAnalyticsService()
except Exception as e:
    logger.error(f"Failed to initialize MetricsAnalyticsService: {str(e)}")
    metrics_service = None


@metrics_router.get('/top-tag-accuracy')
async def get_top_tag_accuracy():
    """
    Calculate and return Top-Tag Accuracy and Perfect Match Rate metrics.

    Top-Tag Accuracy measures how often the highest-confidence AI prediction
    for each hierarchy level (primary, secondary, tertiary) matches the final
    user-confirmed tags.

    Perfect Match Rate measures the percentage of documents where ALL 3 top tags
    (primary, secondary, tertiary) were accepted by the user.

    Returns:
        - top_tag_accuracy: Overall accuracy percentage across all levels
        - perfect_match_rate: Percentage of documents with all 3 top tags accepted
        - top_tag_by_level: Accuracy breakdown by hierarchy level
        - total_documents: Number of documents analyzed
        - documents_with_all_levels: Number of documents with all 3 levels
        - perfect_matches: Number of perfect matches
        - metrics: Detailed acceptance counts for each level
    """
    try:
        if not metrics_service:
            return APIResponse.error(
                "Metrics service not initialized",
                500,
                "SERVICE_UNAVAILABLE"
            )

        logger.info("Calculating top-tag accuracy and perfect match rate metrics")
        result = metrics_service.calculate_top_tag_accuracy()

        return APIResponse.success(
            result,
            f"Metrics calculated - Top-tag accuracy: {result['top_tag_accuracy']}% | "
            f"Perfect match rate: {result['perfect_match_rate']}%"
        )

    except Exception as e:
        error_msg = f"Failed to calculate top-tag accuracy: {str(e)}"
        logger.error(error_msg)
        return APIResponse.error(
            error_msg,
            500,
            "CALCULATION_ERROR"
        )
