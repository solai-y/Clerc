"""
Prompt generation for context-aware classification
"""
from typing import List, Dict, Optional
from hierarchy_validator import HierarchyValidator

class PromptGenerator:
    """Generates context-aware prompts for different prediction scenarios"""
    
    def __init__(self):
        self.validator = HierarchyValidator()
    
    def generate_prompt(self, text: str, predict_levels: List[str], context: Dict[str, str]) -> str:
        """Generate appropriate prompt based on prediction requirements"""
        
        if "primary" in predict_levels:
            return self._generate_full_classification_prompt(text)
        elif "secondary" in predict_levels:
            primary = context.get("primary")
            return self._generate_secondary_tertiary_prompt(text, primary)
        else:  # tertiary only
            primary = context.get("primary")
            secondary = context.get("secondary")
            return self._generate_tertiary_only_prompt(text, primary, secondary)
    
    def _generate_full_classification_prompt(self, text: str) -> str:
        """Generate prompt for complete classification (all levels)"""
        
        # Get all valid paths for explicit hierarchy
        valid_paths = []
        for primary, secondary_dict in self.validator.hierarchy.items():
            for secondary, tertiary_list in secondary_dict.items():
                if tertiary_list:
                    for tertiary in tertiary_list:
                        valid_paths.append(f"  {primary} → {secondary} → {tertiary}")
                else:
                    valid_paths.append(f"  {primary} → {secondary} → {secondary}")
        
        paths_text = "\\n".join(valid_paths)
        
        prompt = f"""You are a senior financial analyst. Classify this document using the EXACT classification path from the list below.

VALID CLASSIFICATION PATHS (Primary → Secondary → Tertiary):
{paths_text}

CLASSIFICATION RULES:
• DISCLOSURE: Official company reports, regulatory filings, earnings statements, operational data
• RECOMMENDATIONS: Investment research, analyst opinions, ratings, price targets, investment advice  
• NEWS: Market news, company announcements, press releases, timely updates

DOCUMENT TO CLASSIFY:
---
{text}
---

STEP-BY-STEP ANALYSIS:
1. What type of document is this? (company report, analyst research, news article)
2. Who is the source? (company, analyst firm, news organization)
3. What is the purpose? (report facts, give investment advice, announce news)
4. Which classification path above best matches?

CONFIDENCE SCORING INSTRUCTIONS:
Use these standardized confidence levels for ALL classifications (primary, secondary, tertiary):

• Very Confident (0.85-1.0): Classification is unambiguous with clear, strong indicators
• Confident (0.70-0.84): Strong indicators present with minor uncertainty
• Moderately Confident (0.55-0.69): Some uncertainty, requires interpretation of context
• Low Confidence (0.40-0.54): Significant uncertainty, limited clear indicators
• Very Low Confidence (0.25-0.39): High uncertainty, ambiguous or conflicting signals

CONFIDENCE FACTORS:
Positive (+confidence): Clear terminology match, identifiable source, explicit purpose, matching structure
Negative (-confidence): Ambiguous language, mixed signals, unclear source/purpose, atypical format

CRITICAL: Choose ONE exact path from the list above. Respond with ONLY this JSON:

{{
    "primary": "EXACT_PRIMARY_NAME",
    "secondary": "EXACT_SECONDARY_NAME",
    "tertiary": "EXACT_TERTIARY_NAME",
    "confidence_primary": 0.87,
    "confidence_secondary": 0.84,
    "confidence_tertiary": 0.81,
    "reasoning": "Brief explanation of why this classification path was chosen and confidence assessment"
}}

Use ONLY the exact category names from the paths above. Apply confidence scoring standards consistently."""
        
        return prompt
    
    def _generate_secondary_tertiary_prompt(self, text: str, primary: str) -> str:
        """Generate prompt for secondary + tertiary prediction given primary"""
        
        if not primary or not self.validator.is_valid_primary(primary):
            # Fallback to full classification
            return self._generate_full_classification_prompt(text)
        
        # Get valid secondary and tertiary options under this primary
        valid_secondaries = self.validator.get_valid_secondaries(primary)
        valid_paths = []
        
        for secondary in valid_secondaries:
            tertiary_list = self.validator.hierarchy[primary][secondary]
            if tertiary_list:
                for tertiary in tertiary_list:
                    valid_paths.append(f"  {secondary} → {tertiary}")
            else:
                valid_paths.append(f"  {secondary} → {secondary}")
        
        paths_text = "\\n".join(valid_paths)
        
        prompt = f"""You are a senior financial analyst. The document has been classified as PRIMARY: {primary}.

Now classify the SECONDARY and TERTIARY levels using ONLY the paths below:

VALID SECONDARY → TERTIARY PATHS:
{paths_text}

DOCUMENT TO CLASSIFY:
---
{text}
---

Given that this is a {primary} document, determine the most specific secondary and tertiary classification.

CONFIDENCE SCORING INSTRUCTIONS:
Use these standardized confidence levels:

• Very Confident (0.85-1.0): Classification is unambiguous with clear, strong indicators
• Confident (0.70-0.84): Strong indicators present with minor uncertainty
• Moderately Confident (0.55-0.69): Some uncertainty, requires interpretation of context
• Low Confidence (0.40-0.54): Significant uncertainty, limited clear indicators
• Very Low Confidence (0.25-0.39): High uncertainty, ambiguous or conflicting signals

CRITICAL: Choose ONE exact path from the list above. Respond with ONLY this JSON:

{{
    "secondary": "EXACT_SECONDARY_NAME",
    "tertiary": "EXACT_TERTIARY_NAME",
    "confidence_secondary": 0.82,
    "confidence_tertiary": 0.78,
    "reasoning": "Brief explanation of why this secondary/tertiary classification was chosen and confidence assessment"
}}

Use ONLY the exact category names from the paths above. Apply confidence scoring standards consistently."""
        
        return prompt
    
    def _generate_tertiary_only_prompt(self, text: str, primary: str, secondary: str) -> str:
        """Generate prompt for tertiary prediction given primary + secondary"""
        
        if not primary or not secondary or not self.validator.is_valid_secondary(primary, secondary):
            # Fallback to full classification
            return self._generate_full_classification_prompt(text)
        
        # Get valid tertiary options under this primary/secondary
        valid_tertiaries = self.validator.get_valid_tertiaries(primary, secondary)
        
        if not valid_tertiaries:
            valid_tertiaries = [secondary]  # Fallback to secondary as tertiary
        
        tertiaries_text = "\\n".join([f"  - {t}" for t in valid_tertiaries])
        
        prompt = f"""You are a senior financial analyst. The document has been classified as:
- PRIMARY: {primary}  
- SECONDARY: {secondary}

Now determine the TERTIARY classification using ONLY the options below:

VALID TERTIARY OPTIONS:
{tertiaries_text}

DOCUMENT TO CLASSIFY:
---
{text}
---

Given that this is a {primary} → {secondary} document, choose the most specific tertiary classification.

CONFIDENCE SCORING INSTRUCTIONS:
Use these standardized confidence levels:

• Very Confident (0.85-1.0): Classification is unambiguous with clear, strong indicators
• Confident (0.70-0.84): Strong indicators present with minor uncertainty
• Moderately Confident (0.55-0.69): Some uncertainty, requires interpretation of context
• Low Confidence (0.40-0.54): Significant uncertainty, limited clear indicators
• Very Low Confidence (0.25-0.39): High uncertainty, ambiguous or conflicting signals

CRITICAL: Choose ONE exact option from the list above. Respond with ONLY this JSON:

{{
    "tertiary": "EXACT_TERTIARY_NAME",
    "confidence_tertiary": 0.75,
    "reasoning": "Brief explanation of why this tertiary classification was chosen and confidence assessment"
}}

Use ONLY the exact category names from the options above. Apply confidence scoring standards consistently."""
        
        return prompt