import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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

    def calculate_top_tag_accuracy(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate Top-Tag Accuracy by comparing highest-confidence AI predictions
        against final user-confirmed tags.

        Args:
            start_date: Start date in YYYY-MM-DD format (Singapore timezone, inclusive)
            end_date: End date in YYYY-MM-DD format (Singapore timezone, inclusive)

        Returns:
            Dict containing:
                - top_tag_accuracy: Overall top-tag accuracy percentage
                - perfect_match_rate: Percentage of documents with all 3 top tags accepted
                - top_tag_by_level: Accuracy broken down by hierarchy level
                - total_documents: Number of documents analyzed
                - date_range: Applied date range filter (if any)
                - metrics: Detailed metrics for each level
        """
        try:
            # Convert Singapore dates to UTC if provided
            date_filter_applied = False
            start_datetime_utc = None
            end_datetime_utc = None

            if start_date or end_date:
                date_filter_applied = True
                # Singapore is UTC+8
                sg_offset = timedelta(hours=8)

                if start_date:
                    # Start of day in Singapore (00:00:00 SGT)
                    start_sg = datetime.strptime(start_date, '%Y-%m-%d')
                    start_datetime_utc = start_sg - sg_offset
                    self.logger.info(f"Start date: {start_date} SGT → {start_datetime_utc.isoformat()}Z UTC")

                if end_date:
                    # End of day in Singapore (23:59:59 SGT)
                    end_sg = datetime.strptime(end_date, '%Y-%m-%d')
                    end_sg = end_sg.replace(hour=23, minute=59, second=59)
                    end_datetime_utc = end_sg - sg_offset
                    self.logger.info(f"End date: {end_date} SGT → {end_datetime_utc.isoformat()}Z UTC")

            # Query processed_documents for suggested_tags and confirmed_tags
            self.logger.info("Fetching processed documents with suggested_tags and confirmed_tags")
            query = self.supabase.table('processed_documents').select(
                'process_id, document_id, suggested_tags, confirmed_tags, reviewed_at'
            ).not_.is_('confirmed_tags', 'null').not_.is_('suggested_tags', 'null')

            # Apply date filters if provided
            if start_datetime_utc:
                query = query.gte('reviewed_at', start_datetime_utc.isoformat() + 'Z')
            if end_datetime_utc:
                query = query.lte('reviewed_at', end_datetime_utc.isoformat() + 'Z')

            response = query.execute()

            if not response.data:
                self.logger.warning("No documents with both suggested_tags and confirmed_tags found")
                result = {
                    "top_tag_accuracy": 0.0,
                    "perfect_match_rate": 0.0,
                    "top_tag_by_level": {
                        "primary": 0.0,
                        "secondary": 0.0,
                        "tertiary": 0.0
                    },
                    "total_documents": 0,
                    "documents_with_all_levels": 0,
                    "perfect_matches": 0,
                    "metrics": {
                        "primary": {"accepted": 0, "total": 0},
                        "secondary": {"accepted": 0, "total": 0},
                        "tertiary": {"accepted": 0, "total": 0}
                    }
                }
                # Add date range info if filter was applied
                if start_date or end_date:
                    result["date_range"] = {
                        "start_date": start_date,
                        "end_date": end_date,
                        "timezone": "Asia/Singapore"
                    }
                return result

            documents = response.data
            self.logger.info(f"Analyzing {len(documents)} documents")

            # Initialize counters for each hierarchy level
            metrics = {
                "primary": {"accepted": 0, "total": 0},
                "secondary": {"accepted": 0, "total": 0},
                "tertiary": {"accepted": 0, "total": 0}
            }

            # Initialize perfect match counters
            perfect_match_count = 0
            documents_with_all_levels = 0

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

                # Track acceptance for each level in this document
                level_acceptance = {}

                # Compare and update metrics for each level
                for level in ['primary', 'secondary', 'tertiary']:
                    if level in top_suggested and top_suggested[level]:
                        top_tag = top_suggested[level]['tag']
                        metrics[level]['total'] += 1

                        # Check if the top-confidence tag was accepted by the user
                        if level in confirmed_by_level and top_tag in confirmed_by_level[level]:
                            metrics[level]['accepted'] += 1
                            level_acceptance[level] = True
                            self.logger.debug(
                                f"Document {doc['document_id']}: {level} tag '{top_tag}' was accepted"
                            )
                        else:
                            level_acceptance[level] = False
                            self.logger.debug(
                                f"Document {doc['document_id']}: {level} tag '{top_tag}' was rejected"
                            )

                # Check if this document has all 3 levels and all were accepted (Perfect Match)
                if len(level_acceptance) == 3:  # Document has all 3 levels
                    documents_with_all_levels += 1
                    if all(level_acceptance.values()):  # All 3 were accepted
                        perfect_match_count += 1
                        self.logger.debug(
                            f"Document {doc['document_id']}: Perfect Match - all 3 top tags accepted"
                        )

            # Calculate accuracy percentages
            top_tag_by_level = {}
            total_accepted = 0
            total_suggested = 0

            for level in ['primary', 'secondary', 'tertiary']:
                accepted = metrics[level]['accepted']
                total = metrics[level]['total']
                total_accepted += accepted
                total_suggested += total

                if total > 0:
                    top_tag_by_level[level] = round((accepted / total) * 100, 2)
                else:
                    top_tag_by_level[level] = 0.0

            # Calculate top tag accuracy
            top_tag_accuracy = round((total_accepted / total_suggested) * 100, 2) if total_suggested > 0 else 0.0

            # Calculate perfect match rate
            perfect_match_rate = round((perfect_match_count / documents_with_all_levels) * 100, 2) if documents_with_all_levels > 0 else 0.0

            result = {
                "top_tag_accuracy": top_tag_accuracy,
                "perfect_match_rate": perfect_match_rate,
                "top_tag_by_level": top_tag_by_level,
                "total_documents": len(documents),
                "documents_with_all_levels": documents_with_all_levels,
                "perfect_matches": perfect_match_count,
                "metrics": metrics
            }

            # Add date range info if filter was applied
            if start_date or end_date:
                result["date_range"] = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "timezone": "Asia/Singapore"
                }

            date_info = ""
            if start_date or end_date:
                date_info = f" | Date range: {start_date or 'start'} to {end_date or 'end'}"

            self.logger.info(
                f"Top-Tag Accuracy: {top_tag_accuracy}% | Perfect Match Rate: {perfect_match_rate}% "
                f"({perfect_match_count}/{documents_with_all_levels}){date_info}"
            )
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
