"""
AI Analysis service for processing cybersecurity content
"""

import json
import time
import asyncio
import aiohttp
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging
from urllib.parse import urljoin

from ..core.config import settings
from ..schemas.analysis_schema import SYSTEM_PROMPT, JSON_SCHEMA
from ..core.logging_config import get_logger

logger = get_logger("analysis")

class AIAnalysisService:
    """Service for analyzing cybersecurity content using local LLaMA server"""
    
    def __init__(self):
        self.base_url = settings.llama_server.base_url
        self.api_key = settings.llama_server.api_key
        self.model_name = settings.llama_server.model_name
        self.timeout = settings.llama_server.timeout
        self.max_retries = settings.llama_server.max_retries
        
    async def analyze_content(
        self, 
        content: str, 
        source_url: str,
        article_metadata: Optional[Dict] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analyze cybersecurity content using AI
        
        Args:
            content: Article content to analyze
            source_url: Source URL of the article
            article_metadata: Additional metadata about the article
            
        Returns:
            Tuple of (analysis_result, error_message)
        """
        start_time = time.time()
        
        try:
            # Validate content length
            if len(content) < settings.min_content_length:
                logger.warning(
                    "Content too short for analysis",
                    content_length=len(content),
                    min_length=settings.min_content_length,
                    source_url=source_url
                )
                return None, "Content too short for analysis"
            
            if len(content) > settings.max_content_length:
                logger.warning(
                    "Content too long, truncating",
                    content_length=len(content),
                    max_length=settings.max_content_length,
                    source_url=source_url
                )
                content = content[:settings.max_content_length]
            
            # Prepare the prompt
            prompt = self._prepare_prompt(content, source_url, article_metadata)
            
            # Make API request with retries
            analysis_result = await self._make_api_request(prompt)
            
            if analysis_result:
                processing_time = time.time() - start_time
                
                # Add metadata to the result
                if "ai_analysis_metadata" in analysis_result:
                    analysis_result["ai_analysis_metadata"].update({
                        "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
                        "ai_model_used": self.model_name,
                        "prompt_version": settings.analysis_prompt_version,
                        "processing_time_seconds": round(processing_time, 2)
                    })
                
                # Add source metadata
                if "source_metadata" in analysis_result:
                    analysis_result["source_metadata"].update({
                        "source_url": source_url,
                        "content_length": len(content)
                    })
                    if article_metadata:
                        analysis_result["source_metadata"].update(article_metadata)
                
                logger.info(
                    "Content analysis completed successfully",
                    source_url=source_url,
                    processing_time=processing_time,
                    content_length=len(content)
                )
                
                return analysis_result, None
            else:
                return None, "Failed to get valid analysis result"
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(
                "Content analysis failed",
                source_url=source_url,
                error=str(e),
                processing_time=processing_time
            )
            return None, error_msg
    
    def _prepare_prompt(self, content: str, source_url: str, metadata: Optional[Dict] = None) -> str:
        """Prepare the prompt for AI analysis"""
        
        # Include source information in the prompt
        source_info = f"Source URL: {source_url}\n"
        if metadata:
            if metadata.get("title"):
                source_info += f"Title: {metadata['title']}\n"
            if metadata.get("publication_date"):
                source_info += f"Publication Date: {metadata['publication_date']}\n"
            if metadata.get("author"):
                source_info += f"Author: {metadata['author']}\n"
        
        prompt = f"""{SYSTEM_PROMPT}

{source_info}

Article Content:
{content}

Please analyze this cybersecurity article and extract information according to the JSON schema. Return only valid JSON without any additional text or formatting."""
        
        return prompt
    
    async def _make_api_request(self, prompt: str) -> Optional[Dict]:
        """Make API request to LLaMA server with retries"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert cybersecurity intelligence analyst. Respond only with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    url = urljoin(self.base_url, "/v1/chat/completions")
                    
                    logger.debug(
                        "Making API request to LLaMA server",
                        attempt=attempt + 1,
                        url=url
                    )
                    
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if "choices" in result and len(result["choices"]) > 0:
                                content = result["choices"][0]["message"]["content"]
                                
                                # Try to parse JSON response
                                try:
                                    analysis_result = json.loads(content)
                                    
                                    # Validate the structure
                                    if self._validate_analysis_result(analysis_result):
                                        return analysis_result
                                    else:
                                        logger.warning(
                                            "Invalid analysis result structure",
                                            attempt=attempt + 1
                                        )
                                        
                                except json.JSONDecodeError as e:
                                    logger.warning(
                                        "Failed to parse JSON response",
                                        attempt=attempt + 1,
                                        error=str(e),
                                        content_preview=content[:200]
                                    )
                        else:
                            logger.warning(
                                "API request failed",
                                attempt=attempt + 1,
                                status_code=response.status,
                                response_text=await response.text()
                            )
                            
            except asyncio.TimeoutError:
                logger.warning(
                    "API request timeout",
                    attempt=attempt + 1,
                    timeout=self.timeout
                )
            except Exception as e:
                logger.warning(
                    "API request error",
                    attempt=attempt + 1,
                    error=str(e)
                )
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        logger.error("All API request attempts failed")
        return None
    
    def _validate_analysis_result(self, result: Dict) -> bool:
        """Validate the structure of analysis result"""
        required_sections = [
            "ai_analysis_metadata",
            "source_metadata", 
            "article_summary_and_context",
            "incident_event_details",
            "threat_actor_and_ttps",
            "vulnerabilities_and_malware",
            "indicators_of_compromise",
            "defensive_measures_and_recommendations",
            "actionable_intelligence_for_playbooks"
        ]
        
        for section in required_sections:
            if section not in result:
                logger.warning(f"Missing required section: {section}")
                return False
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to LLaMA server"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": "Hello, please respond with 'OK'"}
                ],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                url = urljoin(self.base_url, "/v1/chat/completions")
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("LLaMA server connection test successful")
                        return True
                    else:
                        logger.error(f"LLaMA server connection test failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"LLaMA server connection test error: {e}")
            return False

# Global AI analysis service instance
ai_service = AIAnalysisService()