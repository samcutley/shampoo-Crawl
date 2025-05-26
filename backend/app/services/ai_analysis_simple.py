"""
Simplified AI analysis service for demo purposes
"""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager

logger = get_logger("ai_analysis")

class AIAnalysisService:
    """Simplified AI analysis service for demo purposes"""
    
    def __init__(self):
        self.llama_server_url = getattr(settings, 'LLAMA_SERVER_URL', 'http://127.0.0.1:8081')
    
    async def analyze_article(self, article_id: int) -> Dict[str, Any]:
        """Analyze article content and extract threat intelligence"""
        start_time = time.time()
        
        try:
            # Get article from database
            article = self._get_article(article_id)
            if not article:
                raise ValueError(f"Article {article_id} not found")
            
            # For demo purposes, create mock analysis
            analysis_result = self._create_mock_analysis(article)
            
            # Save analysis to database
            self._save_analysis(article_id, analysis_result, time.time() - start_time)
            
            # Update article status
            self._update_article_status(article_id, 'completed')
            
            logger.info(f"Completed analysis for article {article_id}")
            
            return {
                'article_id': article_id,
                'status': 'completed',
                'analysis': analysis_result,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            error_msg = f"Error analyzing article {article_id}: {str(e)}"
            logger.error(error_msg)
            
            # Update article status to failed
            self._update_article_status(article_id, 'failed')
            
            return {
                'article_id': article_id,
                'status': 'failed',
                'error': error_msg,
                'processing_time': time.time() - start_time
            }
    
    def _get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get article from database"""
        try:
            result = db_manager.execute_query(
                "SELECT * FROM articles WHERE id = ?",
                (article_id,)
            )
            
            if result:
                row = result[0]
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'summary': row['summary'],
                    'url': row['url']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")
            return None
    
    def _create_mock_analysis(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock analysis for demo purposes"""
        content = article.get('content', '')
        title = article.get('title', '')
        
        # Mock IOCs based on content keywords
        iocs = []
        if 'malware' in content.lower() or 'ransomware' in content.lower():
            iocs.extend([
                {'type': 'hash', 'value': 'a1b2c3d4e5f6789012345678901234567890abcd', 'confidence': 0.8},
                {'type': 'domain', 'value': 'malicious-domain.com', 'confidence': 0.7}
            ])
        
        if 'phishing' in content.lower():
            iocs.extend([
                {'type': 'url', 'value': 'http://phishing-site.com/login', 'confidence': 0.9},
                {'type': 'email', 'value': 'attacker@evil.com', 'confidence': 0.6}
            ])
        
        # Mock CVEs
        cves = []
        if 'cve-' in content.lower():
            cves.append({
                'cve_id': 'CVE-2024-1234',
                'severity': 'high',
                'description': 'Mock vulnerability found in content'
            })
        
        # Mock threat actors
        threat_actors = []
        if any(actor in content.lower() for actor in ['apt', 'lazarus', 'carbanak']):
            threat_actors.append({
                'name': 'APT-Demo',
                'motivation': 'financial',
                'confidence': 'medium'
            })
        
        # Mock severity assessment
        severity = 'low'
        if any(keyword in content.lower() for keyword in ['critical', 'zero-day', 'ransomware']):
            severity = 'critical'
        elif any(keyword in content.lower() for keyword in ['high', 'exploit', 'breach']):
            severity = 'high'
        elif any(keyword in content.lower() for keyword in ['medium', 'vulnerability', 'attack']):
            severity = 'medium'
        
        return {
            'summary': f"Analysis of: {title[:100]}...",
            'severity': severity,
            'confidence_score': 0.75,
            'iocs': iocs,
            'cves': cves,
            'threat_actors': threat_actors,
            'malware_families': [],
            'industries_targeted': ['technology', 'finance'],
            'regions_affected': ['global'],
            'attack_techniques': ['phishing', 'malware'],
            'recommendations': [
                'Update security patches',
                'Monitor for IOCs',
                'Implement additional security controls'
            ],
            'tags': ['cybersecurity', 'threat-intelligence'],
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _save_analysis(self, article_id: int, analysis: Dict[str, Any], processing_time: float):
        """Save analysis to database"""
        try:
            # Save main analysis
            query = """
                INSERT INTO ai_analysis (article_id, analysis_data, confidence_score, 
                                       processing_time_seconds, ai_model_used, prompt_version)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            params = (
                article_id,
                json.dumps(analysis),
                analysis.get('confidence_score', 0.0),
                processing_time,
                'mock-ai-model',
                'v1.0'
            )
            
            db_manager.execute_insert(query, params)
            
            # Save IOCs
            for ioc in analysis.get('iocs', []):
                ioc_query = """
                    INSERT INTO iocs (article_id, ioc_type, ioc_value, confidence_score)
                    VALUES (?, ?, ?, ?)
                """
                ioc_params = (
                    article_id,
                    ioc['type'],
                    ioc['value'],
                    ioc['confidence']
                )
                db_manager.execute_insert(ioc_query, ioc_params)
            
            # Save CVEs
            for cve in analysis.get('cves', []):
                cve_query = """
                    INSERT INTO cves (article_id, cve_id, description, severity)
                    VALUES (?, ?, ?, ?)
                """
                cve_params = (
                    article_id,
                    cve['cve_id'],
                    cve['description'],
                    cve['severity']
                )
                db_manager.execute_insert(cve_query, cve_params)
            
            # Save threat actors
            for actor in analysis.get('threat_actors', []):
                actor_query = """
                    INSERT INTO threat_actors (article_id, actor_name, motivation, attribution_confidence)
                    VALUES (?, ?, ?, ?)
                """
                actor_params = (
                    article_id,
                    actor['name'],
                    actor['motivation'],
                    actor['confidence']
                )
                db_manager.execute_insert(actor_query, actor_params)
            
        except Exception as e:
            logger.error(f"Error saving analysis for article {article_id}: {e}")
            raise
    
    def _update_article_status(self, article_id: int, status: str):
        """Update article analysis status"""
        try:
            query = "UPDATE articles SET analysis_status = ?, updated_at = ? WHERE id = ?"
            params = (status, datetime.utcnow(), article_id)
            db_manager.execute_insert(query, params)
        except Exception as e:
            logger.error(f"Error updating article status for {article_id}: {e}")

# Global service instance
ai_analysis_service = AIAnalysisService()