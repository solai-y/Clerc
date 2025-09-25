"""
Database service for prediction service configuration
"""
import os
import logging
from typing import Dict, Optional, Tuple
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for managing prediction service configuration"""
    
    def __init__(self):
        """Initialize database connection"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Database service initialized")
    
    def get_confidence_thresholds(self) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
        """
        Get current confidence thresholds from database
        
        Returns:
            Tuple of (thresholds_dict, error_message)
        """
        try:
            # Get the most recent threshold configuration
            response = self.supabase.table('confidence_thresholds').select(
                'primary_threshold, secondary_threshold, tertiary_threshold, updated_at'
            ).order('updated_at', desc=True).limit(1).execute()
            
            if not response.data:
                # No thresholds found, return defaults
                logger.warning("No confidence thresholds found in database, using defaults")
                return {
                    "primary": 0.85,
                    "secondary": 0.80,
                    "tertiary": 0.75
                }, None
            
            threshold_row = response.data[0]
            thresholds = {
                "primary": float(threshold_row["primary_threshold"]),
                "secondary": float(threshold_row["secondary_threshold"]),
                "tertiary": float(threshold_row["tertiary_threshold"])
            }
            
            logger.info(f"Retrieved confidence thresholds: {thresholds}")
            return thresholds, None
            
        except Exception as e:
            error_msg = f"Failed to retrieve confidence thresholds: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def update_confidence_thresholds(
        self, 
        primary: Optional[float] = None,
        secondary: Optional[float] = None,
        tertiary: Optional[float] = None,
        updated_by: str = "api"
    ) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
        """
        Update confidence thresholds in database
        
        Args:
            primary: Primary threshold (0.0-1.0)
            secondary: Secondary threshold (0.0-1.0)
            tertiary: Tertiary threshold (0.0-1.0)
            updated_by: User or system that made the update
            
        Returns:
            Tuple of (updated_thresholds_dict, error_message)
        """
        try:
            # Validate thresholds
            for name, value in [("primary", primary), ("secondary", secondary), ("tertiary", tertiary)]:
                if value is not None:
                    if not (0.0 <= value <= 1.0):
                        return None, f"Invalid {name} threshold: {value}. Must be between 0.0 and 1.0"
            
            # Get current thresholds first
            current_thresholds, error = self.get_confidence_thresholds()
            if error:
                return None, f"Failed to get current thresholds: {error}"
            
            # Build update data with only provided values
            update_data = {"updated_by": updated_by}
            final_thresholds = current_thresholds.copy()
            
            if primary is not None:
                update_data["primary_threshold"] = primary
                final_thresholds["primary"] = primary
            if secondary is not None:
                update_data["secondary_threshold"] = secondary
                final_thresholds["secondary"] = secondary
            if tertiary is not None:
                update_data["tertiary_threshold"] = tertiary
                final_thresholds["tertiary"] = tertiary
            
            
            # Insert new threshold configuration
            response = self.supabase.table('confidence_thresholds').insert(update_data).execute()
            
            if not response.data:
                return None, "Failed to insert threshold configuration"
            
            logger.info(f"Updated confidence thresholds: {final_thresholds} by {updated_by}")
            return final_thresholds, None
            
        except Exception as e:
            error_msg = f"Failed to update confidence thresholds: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_threshold_history(self, limit: int = 10) -> Tuple[Optional[list], Optional[str]]:
        """
        Get history of threshold changes
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (history_list, error_message)
        """
        try:
            response = self.supabase.table('confidence_thresholds').select(
                'primary_threshold, secondary_threshold, tertiary_threshold, updated_at, updated_by'
            ).order('updated_at', desc=True).limit(limit).execute()
            
            if not response.data:
                return [], None
            
            history = []
            for row in response.data:
                history.append({
                    "primary_threshold": float(row["primary_threshold"]),
                    "secondary_threshold": float(row["secondary_threshold"]),
                    "tertiary_threshold": float(row["tertiary_threshold"]),
                    "updated_at": row["updated_at"],
                    "updated_by": row["updated_by"]
                })
            
            logger.info(f"Retrieved {len(history)} threshold history records")
            return history, None
            
        except Exception as e:
            error_msg = f"Failed to retrieve threshold history: {str(e)}"
            logger.error(error_msg)
            return None, error_msg