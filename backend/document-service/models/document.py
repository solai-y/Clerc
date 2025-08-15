import re
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentModel:
    """Document model with validation and sanitization"""
    
    def __init__(self, data: Dict[str, Any]):
        self.document_id = data.get('document_id')
        self.document_name = self._sanitize_string(data.get('document_name', ''))
        self.document_type = self._sanitize_string(data.get('document_type', ''))
        self.link = self._sanitize_string(data.get('link', ''))
        self.categories = data.get('categories', [])
        self.upload_date = self._validate_date(data.get('upload_date'))
        self.uploaded_by = self._validate_integer(data.get('uploaded_by'))
        self.company = self._validate_integer(data.get('company'))
    
    def _sanitize_string(self, value: Any) -> str:
        """Sanitize string input"""
        if value is None:
            return ''
        
        # Convert to string and strip whitespace
        clean_value = str(value).strip()
        
        # Remove any potentially harmful characters
        clean_value = re.sub(r'[<>"\']', '', clean_value)
        
        return clean_value[:255]  # Limit length
    
    def _validate_integer(self, value: Any) -> Optional[int]:
        """Validate and convert to integer"""
        if value is None:
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _validate_date(self, value: Any) -> Optional[str]:
        """Validate date format"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Try to parse ISO format
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return value
            except ValueError:
                return None
        
        return None
    
    def validate(self) -> tuple[bool, list]:
        """Validate the document model"""
        errors = []
        
        if not self.document_name:
            errors.append("Document name is required")
        
        if not self.document_type:
            errors.append("Document type is required")
        
        if not self.link:
            errors.append("Link is required")
        
        if self.uploaded_by is None:
            errors.append("Uploaded by user ID is required")
        
        if self.company is None:
            errors.append("Company ID is required")
        
        # Validate categories is a list
        if self.categories is not None and not isinstance(self.categories, list):
            errors.append("Categories must be a list")
        
        return len(errors) == 0, errors
    
    def to_dict(self, include_id: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary for database operations"""
        data = {
            'document_name': self.document_name,
            'document_type': self.document_type,
            'link': self.link,
            'uploaded_by': self.uploaded_by,
            'company': self.company
        }
        
        # Include optional fields if they exist
        if include_id and self.document_id is not None:
            data['document_id'] = self.document_id
        if self.categories is not None:
            data['categories'] = self.categories
        if self.upload_date is not None:
            data['upload_date'] = self.upload_date
        
        return data