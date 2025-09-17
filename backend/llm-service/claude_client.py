"""
Claude Sonnet 4 client for document classification
"""
import json
import time
import logging
import random
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from config import Config

logger = logging.getLogger(__name__)

class ClaudeClient:
    """Client for interacting with Claude Sonnet 4 via AWS Bedrock"""
    
    def __init__(self):
        self.model_id = Config.CLAUDE_MODEL_ID
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY_SECONDS
        self.timeout = Config.REQUEST_TIMEOUT_SECONDS
        
        # Initialize Bedrock client
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        
        logger.info(f"Initialized Claude client with model: {self.model_id}")
    
    def classify_with_retry(self, prompt: str) -> Dict[str, Any]:
        """
        Classify document with retry logic until success
        
        Args:
            prompt: The classification prompt
            
        Returns:
            Parsed classification result
            
        Raises:
            Exception: Only after exhausting all retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Classification attempt {attempt + 1}/{self.max_retries}")
                result = self._make_classification_request(prompt)
                logger.info("Classification successful")
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Add jitter to retry delay
                    delay = self.retry_delay + random.uniform(0, 5)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        # If we get here, all retries failed
        raise Exception(f"Classification failed after {self.max_retries} attempts. Last error: {str(last_exception)}")
    
    def _make_classification_request(self, prompt: str) -> Dict[str, Any]:
        """
        Make a single classification request to Claude
        
        Args:
            prompt: The classification prompt
            
        Returns:
            Parsed classification result
        """
        try:
            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.0,
                "top_p": 1.0,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Make request to Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' not in response_body or not response_body['content']:
                raise Exception("Empty response from Claude")
            
            # Extract text content
            content = response_body['content'][0]['text']
            
            # Log Claude's raw response
            logger.info("=== CLAUDE'S RAW RESPONSE ===")
            logger.info(content)
            logger.info("=== END RAW RESPONSE ===")
            
            # Parse JSON from Claude's response
            parsed_result = self._parse_claude_response(content)
            
            # Log the parsed result
            logger.info("=== PARSED CLAUDE RESULT ===")
            logger.info(json.dumps(parsed_result, indent=2))
            logger.info("=== END PARSED RESULT ===")
            
            return parsed_result
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                raise Exception(f"API throttling: {str(e)}")
            elif error_code == 'AccessDeniedException':
                raise Exception(f"Access denied: {str(e)}")
            else:
                raise Exception(f"AWS Bedrock error ({error_code}): {str(e)}")
        
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Bedrock response: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    def _parse_claude_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response and extract classification JSON
        
        Args:
            content: Raw text response from Claude
            
        Returns:
            Parsed classification dictionary
        """
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_content = content.strip()
            
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content[3:]
            
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            
            cleaned_content = cleaned_content.strip()
            
            # Try to parse as JSON
            result = json.loads(cleaned_content)
            
            # Validate required fields exist
            if not isinstance(result, dict):
                raise Exception("Response is not a JSON object")
            
            return result
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract JSON from the content
            import re
            
            # Look for JSON-like structure in the content
            json_match = re.search(r'\\{[^}]*\\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            raise Exception(f"Could not parse Claude response as JSON: {str(e)}. Content: {content[:200]}...")
    
    # Removed generate_mock_evidence method - no longer needed