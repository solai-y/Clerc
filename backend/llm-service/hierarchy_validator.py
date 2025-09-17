"""
Hierarchy validation utilities
"""
from typing import Optional, List, Dict, Any
from config import TAG_HIERARCHY

class HierarchyValidator:
    """Validates predictions against the tag hierarchy"""
    
    def __init__(self):
        self.hierarchy = TAG_HIERARCHY
    
    def get_valid_primaries(self) -> List[str]:
        """Get all valid primary tags"""
        return list(self.hierarchy.keys())
    
    def get_valid_secondaries(self, primary: Optional[str] = None) -> List[str]:
        """Get valid secondary tags, optionally filtered by primary"""
        if primary is None:
            # Return all secondaries from all primaries
            secondaries = []
            for primary_tags in self.hierarchy.values():
                secondaries.extend(primary_tags.keys())
            return list(set(secondaries))
        
        if primary not in self.hierarchy:
            return []
        
        return list(self.hierarchy[primary].keys())
    
    def get_valid_tertiaries(self, primary: Optional[str] = None, secondary: Optional[str] = None) -> List[str]:
        """Get valid tertiary tags, optionally filtered by primary/secondary"""
        if primary is None and secondary is None:
            # Return all tertiaries from all paths
            tertiaries = []
            for primary_tags in self.hierarchy.values():
                for secondary_tags in primary_tags.values():
                    if isinstance(secondary_tags, list):
                        tertiaries.extend(secondary_tags)
            return list(set(tertiaries))
        
        if primary is not None and secondary is not None:
            # Return tertiaries for specific primary/secondary combination
            if primary not in self.hierarchy:
                return []
            if secondary not in self.hierarchy[primary]:
                return []
            
            tertiary_list = self.hierarchy[primary][secondary]
            # If no tertiaries defined, return secondary as tertiary
            return tertiary_list if tertiary_list else [secondary]
        
        if primary is not None:
            # Return all tertiaries under this primary
            if primary not in self.hierarchy:
                return []
            
            tertiaries = []
            for secondary, tertiary_list in self.hierarchy[primary].items():
                if tertiary_list:
                    tertiaries.extend(tertiary_list)
                else:
                    tertiaries.append(secondary)
            return list(set(tertiaries))
        
        return []
    
    def is_valid_primary(self, primary: str) -> bool:
        """Check if primary tag is valid"""
        return primary in self.hierarchy
    
    def is_valid_secondary(self, primary: str, secondary: str) -> bool:
        """Check if secondary tag is valid under given primary"""
        if not self.is_valid_primary(primary):
            return False
        return secondary in self.hierarchy[primary]
    
    def is_valid_tertiary(self, primary: str, secondary: str, tertiary: str) -> bool:
        """Check if tertiary tag is valid under given primary/secondary"""
        if not self.is_valid_secondary(primary, secondary):
            return False
        
        valid_tertiaries = self.hierarchy[primary][secondary]
        # If no tertiaries defined, secondary itself is valid as tertiary
        if not valid_tertiaries:
            return tertiary == secondary
        
        return tertiary in valid_tertiaries
    
    def get_best_fit_primary(self, predicted_primary: str) -> str:
        """Get best fit primary tag if prediction is invalid"""
        valid_primaries = self.get_valid_primaries()
        
        # If the prediction is valid, return it
        if predicted_primary in valid_primaries:
            return predicted_primary
        
        # Simple fallback: return first primary (could be enhanced with similarity matching)
        return valid_primaries[0] if valid_primaries else "Disclosure"
    
    def get_best_fit_secondary(self, primary: str, predicted_secondary: str) -> str:
        """Get best fit secondary tag if prediction is invalid"""
        valid_secondaries = self.get_valid_secondaries(primary)
        
        # If the prediction is valid, return it
        if predicted_secondary in valid_secondaries:
            return predicted_secondary
        
        # Simple fallback: return first secondary under this primary
        return valid_secondaries[0] if valid_secondaries else "Annual_Reports"
    
    def get_best_fit_tertiary(self, primary: str, secondary: str, predicted_tertiary: str) -> str:
        """Get best fit tertiary tag if prediction is invalid"""
        valid_tertiaries = self.get_valid_tertiaries(primary, secondary)
        
        # If the prediction is valid, return it
        if predicted_tertiary in valid_tertiaries:
            return predicted_tertiary
        
        # Simple fallback: return first tertiary or secondary if no tertiaries
        if valid_tertiaries:
            return valid_tertiaries[0]
        else:
            return secondary
    
    def validate_and_fix_prediction(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix a complete prediction"""
        result = prediction.copy()
        
        # Fix primary if needed
        if 'primary' in result:
            original_primary = result['primary']
            fixed_primary = self.get_best_fit_primary(original_primary)
            result['primary'] = fixed_primary
            
            # Fix secondary if needed
            if 'secondary' in result:
                original_secondary = result['secondary']
                fixed_secondary = self.get_best_fit_secondary(fixed_primary, original_secondary)
                result['secondary'] = fixed_secondary
                
                # Fix tertiary if needed
                if 'tertiary' in result:
                    original_tertiary = result['tertiary']
                    fixed_tertiary = self.get_best_fit_tertiary(fixed_primary, fixed_secondary, original_tertiary)
                    result['tertiary'] = fixed_tertiary
        
        return result