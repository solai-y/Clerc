"""
Tag Service Client for fetching dynamic tag hierarchy
"""
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TagServiceClient:
    """Client for communicating with tag service"""

    def __init__(self, base_url: str = "http://tag-service:5007"):
        self.base_url = base_url
        self.timeout = 10.0
        logger.info(f"Tag service client initialized with base URL: {base_url}")

    def fetch_hierarchy(self) -> Dict[str, Any]:
        """
        Fetch the complete tag hierarchy from tag service

        Returns:
            Dictionary in format: { "Primary": { "Secondary": ["tertiary1", ...], ... }, ... }

        Raises:
            Exception: If tag service is unreachable or returns invalid data
        """
        try:
            logger.info(f"Fetching tag hierarchy from: {self.base_url}/tags")

            # Use httpx synchronously (since this is called during request processing)
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/tags")
                response.raise_for_status()

                hierarchy = response.json()

                # Validate the structure
                if not isinstance(hierarchy, dict):
                    raise ValueError("Tag hierarchy must be a dictionary")

                # Log summary
                primary_count = len(hierarchy)
                secondary_count = sum(len(secondaries) for secondaries in hierarchy.values())
                tertiary_count = sum(
                    len(tertiaries)
                    for secondaries in hierarchy.values()
                    for tertiaries in secondaries.values()
                )

                logger.info(
                    f"Successfully fetched tag hierarchy: "
                    f"{primary_count} primary, {secondary_count} secondary, {tertiary_count} tertiary tags"
                )

                return hierarchy

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from tag service"
            try:
                error_detail = e.response.json().get("detail", "Unknown error")
                error_msg += f": {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise Exception(error_msg)

        except httpx.RequestError as e:
            error_msg = f"Network error connecting to tag service: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Failed to fetch tag hierarchy: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of tag service

        Returns:
            Health status information
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/tags")
                response.raise_for_status()
                return {"status": "healthy", "reachable": True}
        except Exception as e:
            logger.error(f"Tag service health check failed: {str(e)}")
            return {"status": "unhealthy", "reachable": False, "error": str(e)}
