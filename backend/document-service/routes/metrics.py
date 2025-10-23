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
    Calculate and return Top-Tag Accuracy metrics.

    Top-Tag Accuracy measures how often the highest-confidence AI prediction
    for each hierarchy level (primary, secondary, tertiary) matches the final
    user-confirmed tags.

    Returns:
        - overall_accuracy: Overall accuracy percentage across all levels
        - by_level: Accuracy breakdown by hierarchy level
        - total_documents: Number of documents analyzed
        - metrics: Detailed acceptance counts for each level
    """
    try:
        if not metrics_service:
            return APIResponse.error(
                "Metrics service not initialized",
                500,
                "SERVICE_UNAVAILABLE"
            )

        logger.info("Calculating top-tag accuracy metrics")
        result = metrics_service.calculate_top_tag_accuracy()

        return APIResponse.success(
            result,
            f"Top-tag accuracy calculated: {result['overall_accuracy']}%"
        )

    except Exception as e:
        error_msg = f"Failed to calculate top-tag accuracy: {str(e)}"
        logger.error(error_msg)
        return APIResponse.error(
            error_msg,
            500,
            "CALCULATION_ERROR"
        )
