import os
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class MetricsAnalyticsService:
    """Service for calculating tag prediction accuracy metrics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("MetricsAnalyticsService initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics analytics service: {str(e)}")
            raise

    def calculate_top_tag_accuracy(self) -> Dict[str, Any]:
        """
        Calculate Top-Tag Accuracy by comparing highest-confidence AI predictions
        against final user-confirmed tags.

        Returns:
            Dict containing:
                - overall_accuracy: Overall top-tag accuracy percentage
                - by_level: Accuracy broken down by hierarchy level (primary, secondary, tertiary)
                - total_documents: Number of documents analyzed
                - metrics: Detailed metrics for each level
        """
        try:
            # Query processed_documents for suggested_tags and confirmed_tags
            self.logger.info("Fetching processed documents with suggested_tags and confirmed_tags")
            response = self.supabase.table('processed_documents').select(
                'process_id, document_id, suggested_tags, confirmed_tags'
            ).not_.is_('confirmed_tags', 'null').not_.is_('suggested_tags', 'null').execute()

            if not response.data:
                self.logger.warning("No documents with both suggested_tags and confirmed_tags found")
                return {
                    "overall_accuracy": 0.0,
                    "by_level": {
                        "primary": 0.0,
                        "secondary": 0.0,
                        "tertiary": 0.0
                    },
                    "total_documents": 0,
                    "metrics": {
                        "primary": {"accepted": 0, "total": 0},
                        "secondary": {"accepted": 0, "total": 0},
                        "tertiary": {"accepted": 0, "total": 0}
                    }
                }

            documents = response.data
            self.logger.info(f"Analyzing {len(documents)} documents")

            # Initialize counters for each hierarchy level
            metrics = {
                "primary": {"accepted": 0, "total": 0},
                "secondary": {"accepted": 0, "total": 0},
                "tertiary": {"accepted": 0, "total": 0}
            }

            # Process each document
            for doc in documents:
                suggested_tags = doc.get('suggested_tags')
                confirmed_tags = doc.get('confirmed_tags')

                if not suggested_tags or not confirmed_tags:
                    continue

                # Extract highest confidence tags from suggested_tags for each level
                top_suggested = self._get_top_confidence_tags_by_level(suggested_tags)

                # Extract confirmed tags for each level
                confirmed_by_level = self._get_confirmed_tags_by_level(confirmed_tags)

                # Compare and update metrics for each level
                for level in ['primary', 'secondary', 'tertiary']:
                    if level in top_suggested and top_suggested[level]:
                        top_tag = top_suggested[level]['tag']
                        metrics[level]['total'] += 1

                        # Check if the top-confidence tag was accepted by the user
                        if level in confirmed_by_level and top_tag in confirmed_by_level[level]:
                            metrics[level]['accepted'] += 1
                            self.logger.debug(
                                f"Document {doc['document_id']}: {level} tag '{top_tag}' was accepted"
                            )
                        else:
                            self.logger.debug(
                                f"Document {doc['document_id']}: {level} tag '{top_tag}' was rejected"
                            )

            # Calculate accuracy percentages
            accuracy_by_level = {}
            total_accepted = 0
            total_suggested = 0

            for level in ['primary', 'secondary', 'tertiary']:
                accepted = metrics[level]['accepted']
                total = metrics[level]['total']
                total_accepted += accepted
                total_suggested += total

                if total > 0:
                    accuracy_by_level[level] = round((accepted / total) * 100, 2)
                else:
                    accuracy_by_level[level] = 0.0

            # Calculate overall accuracy
            overall_accuracy = round((total_accepted / total_suggested) * 100, 2) if total_suggested > 0 else 0.0

            result = {
                "overall_accuracy": overall_accuracy,
                "by_level": accuracy_by_level,
                "total_documents": len(documents),
                "metrics": metrics
            }

            self.logger.info(f"Top-Tag Accuracy calculated: {overall_accuracy}%")
            return result

        except Exception as e:
            error_msg = f"Failed to calculate top-tag accuracy: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _get_top_confidence_tags_by_level(self, suggested_tags: Any) -> Dict[str, Dict[str, Any]]:
        """
        Extract the highest confidence tag for each hierarchy level from suggested_tags.

        Args:
            suggested_tags: Can be a list or dict with nested structure

        Returns:
            Dict mapping level -> {tag, confidence, source}
        """
        top_tags = {}

        try:
            # suggested_tags can be an array or a nested structure
            tags_list = []

            if isinstance(suggested_tags, list):
                tags_list = suggested_tags
            elif isinstance(suggested_tags, dict):
                # Handle nested structure like {tags: [...]} or {suggested_tags: {tags: [...]}}
                if 'tags' in suggested_tags:
                    tags_list = suggested_tags['tags']
                elif 'suggested_tags' in suggested_tags and isinstance(suggested_tags['suggested_tags'], dict):
                    tags_list = suggested_tags['suggested_tags'].get('tags', [])

            # Find highest confidence tag for each level
            for tag_obj in tags_list:
                if not isinstance(tag_obj, dict):
                    continue

                # Extract fields (handle different naming conventions)
                tag_name = tag_obj.get('tag')
                level = tag_obj.get('hierarchy_level') or tag_obj.get('level')
                confidence = tag_obj.get('score') or tag_obj.get('confidence', 0)
                source = tag_obj.get('source', 'ai')

                if not tag_name or not level:
                    continue

                # Normalize level name
                level = level.lower()
                if level not in ['primary', 'secondary', 'tertiary']:
                    continue

                # Keep track of highest confidence tag for this level
                if level not in top_tags or confidence > top_tags[level]['confidence']:
                    top_tags[level] = {
                        'tag': tag_name,
                        'confidence': confidence,
                        'source': source
                    }

        except Exception as e:
            self.logger.warning(f"Error parsing suggested_tags: {e}")

        return top_tags

    def _get_confirmed_tags_by_level(self, confirmed_tags: Any) -> Dict[str, List[str]]:
        """
        Extract confirmed tags grouped by hierarchy level.

        Args:
            confirmed_tags: Can be a list or dict with nested structure

        Returns:
            Dict mapping level -> [list of tag names]
        """
        tags_by_level = {
            'primary': [],
            'secondary': [],
            'tertiary': []
        }

        try:
            # confirmed_tags can be an array or nested structure
            tags_list = []

            if isinstance(confirmed_tags, list):
                tags_list = confirmed_tags
            elif isinstance(confirmed_tags, dict):
                # Handle nested structure like {tags: [...]} or {confirmed_tags: {tags: [...]}}
                if 'tags' in confirmed_tags:
                    tags_list = confirmed_tags['tags']
                elif 'confirmed_tags' in confirmed_tags and isinstance(confirmed_tags['confirmed_tags'], dict):
                    tags_list = confirmed_tags['confirmed_tags'].get('tags', [])

            # Group tags by level
            for tag_obj in tags_list:
                if not isinstance(tag_obj, dict):
                    continue

                tag_name = tag_obj.get('tag')
                level = tag_obj.get('level')

                if not tag_name or not level:
                    continue

                # Normalize level name
                level = level.lower()
                if level in tags_by_level:
                    tags_by_level[level].append(tag_name)

        except Exception as e:
            self.logger.warning(f"Error parsing confirmed_tags: {e}")

        return tags_by_level
