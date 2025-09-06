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
        self.upload_date = self._validate_date(data.get('upload_date'))
        self.uploaded_by = self._validate_integer(data.get('uploaded_by'))
        self.file_size = self._validate_integer(data.get('file_size'))
        self.file_hash = self._sanitize_string(data.get('file_hash', ''))
        self.status = self._sanitize_string(data.get('status', 'uploaded'))
    
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
        
        # uploaded_by and company are now optional since login isn't implemented yet
        
        # Validate status values
        valid_statuses = ['uploaded', 'processing', 'processed', 'failed']
        if self.status and self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return len(errors) == 0, errors
    
    def to_dict(self, include_id: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary for database operations"""
        data = {
            'document_name': self.document_name,
            'document_type': self.document_type,
            'link': self.link,
            'uploaded_by': self.uploaded_by,
            'status': self.status
        }
        
        # Include optional fields if they exist
        if include_id and self.document_id is not None:
            data['document_id'] = self.document_id
        if self.file_size is not None:
            data['file_size'] = self.file_size
        if self.file_hash:
            data['file_hash'] = self.file_hash
        if self.upload_date is not None:
            data['upload_date'] = self.upload_date
        
        return data