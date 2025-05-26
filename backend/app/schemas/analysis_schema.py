"""
Enhanced JSON schema for cybersecurity intelligence extraction.
This schema is designed to capture comprehensive threat intelligence data.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class PostType(str, Enum):
    INCIDENT_REPORT = "Incident Report"
    THREAT_ACTOR_PROFILE = "Threat Actor Profile"
    VULNERABILITY_ANALYSIS = "Vulnerability Analysis"
    MALWARE_DEEP_DIVE = "Malware Deep Dive"
    SECURITY_ADVISORY = "Security Advisory"
    NEWS_BRIEF = "News Brief"
    RESEARCH_PAPER = "Research Paper"
    PRODUCT_REVIEW = "Product Review"
    THREAT_LANDSCAPE_REPORT = "Threat Landscape Report"
    OTHER = "Other"

class StoryDepth(str, Enum):
    OVERVIEW_BRIEF = "Overview/Brief"
    GENERAL_TECHNICAL = "General Technical"
    DETAILED_ANALYSIS = "Detailed Analysis"
    DEEP_DIVE_FORENSIC = "Deep Dive/Forensic"
    STRATEGIC_EXECUTIVE = "Strategic/Executive Summary"

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"
    NOT_SPECIFIED = "Not Specified"

class ActionabilityLevel(str, Enum):
    IMMEDIATE_ACTION = "Immediate Action Required"
    HIGH_PRIORITY = "High Priority Awareness"
    OPERATIONAL_REVIEW = "Operational Review"
    INFORMATIONAL = "Informational/Contextual"
    STRATEGIC = "Strategic Consideration"

class AIAnalysisMetadata(BaseModel):
    analysis_timestamp: str = Field(..., description="ISO 8601 format timestamp")
    ai_model_used: str = Field(..., description="Name of the AI model used")
    prompt_version: str = Field(..., description="Version of the extraction prompt")
    confidence_in_analysis: ConfidenceLevel = Field(..., description="AI confidence in analysis")
    is_likely_primary_source: bool = Field(..., description="Whether article is primary source")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken for analysis")
    extraction_completeness_score: Optional[float] = Field(None, description="0-1 score of extraction completeness")

class ArticleSummaryAndContext(BaseModel):
    story_summary: str = Field(..., description="Concise summary of main points")
    post_type: PostType = Field(..., description="Primary nature of the article")
    tags: List[str] = Field(default_factory=list, description="Relevant keywords and tags")
    story_depth: StoryDepth = Field(..., description="Level of technical detail")
    target_audience_relevance: List[str] = Field(default_factory=list, description="Primary audience")
    key_takeaways: List[str] = Field(default_factory=list, description="Main conclusions")
    language_detected: Optional[str] = Field(None, description="Primary language of content")
    content_quality_score: Optional[float] = Field(None, description="0-1 score of content quality")

class IncidentEventDetails(BaseModel):
    incident_date_approx: str = Field(..., description="Approximate incident date")
    disclosure_date_approx: str = Field(..., description="Approximate disclosure date")
    regions_impacted: List[str] = Field(default_factory=list, description="Geographic regions affected")
    industry_targeted: List[str] = Field(default_factory=list, description="Industries affected")
    impact_description: str = Field(..., description="Description of impact")
    severity_assessment: SeverityLevel = Field(..., description="Assessed severity")
    estimated_financial_impact: Optional[str] = Field(None, description="Financial impact if mentioned")
    affected_user_count: Optional[str] = Field(None, description="Number of users affected")
    business_disruption_duration: Optional[str] = Field(None, description="Duration of disruption")

class ThreatActorAndTTPs(BaseModel):
    attacker_group_suspected: List[str] = Field(default_factory=list, description="Suspected threat actors")
    attacker_motivation: str = Field(..., description="Inferred motivation")
    ttps_observed_mitre: List[str] = Field(default_factory=list, description="MITRE ATT&CK technique IDs")
    ttps_observed_descriptive: List[str] = Field(default_factory=list, description="Descriptive TTPs")
    novel_techniques_highlighted: List[str] = Field(default_factory=list, description="Novel techniques")
    attribution_confidence: Optional[ConfidenceLevel] = Field(None, description="Confidence in attribution")
    campaign_names: List[str] = Field(default_factory=list, description="Named campaigns")
    infrastructure_details: List[str] = Field(default_factory=list, description="Infrastructure used")

class VulnerabilitiesAndMalware(BaseModel):
    vulnerabilities_exploited_desc: List[str] = Field(default_factory=list, description="Vulnerability descriptions")
    cve_ids_mentioned: List[str] = Field(default_factory=list, description="CVE identifiers")
    malware_families_involved: List[str] = Field(default_factory=list, description="Malware families")
    targeted_technologies_platforms: List[str] = Field(default_factory=list, description="Targeted platforms")
    exploit_availability: Optional[str] = Field(None, description="Exploit availability status")
    patch_availability: Optional[str] = Field(None, description="Patch availability status")
    zero_day_indicators: List[str] = Field(default_factory=list, description="Zero-day indicators")

class HashesModel(BaseModel):
    md5: List[str] = Field(default_factory=list)
    sha1: List[str] = Field(default_factory=list)
    sha256: List[str] = Field(default_factory=list)
    sha512: List[str] = Field(default_factory=list)

class IndicatorsOfCompromise(BaseModel):
    ips: List[str] = Field(default_factory=list, description="IP addresses")
    domains: List[str] = Field(default_factory=list, description="Domain names")
    urls: List[str] = Field(default_factory=list, description="Full URLs")
    hashes: HashesModel = Field(default_factory=HashesModel, description="File hashes")
    email_addresses: List[str] = Field(default_factory=list, description="Email addresses")
    file_names: List[str] = Field(default_factory=list, description="Malicious file names")
    registry_keys: List[str] = Field(default_factory=list, description="Registry keys")
    mutexes: List[str] = Field(default_factory=list, description="Mutex names")
    other_iocs_desc: List[str] = Field(default_factory=list, description="Other IOCs")
    yara_rules: List[str] = Field(default_factory=list, description="YARA rules mentioned")
    network_signatures: List[str] = Field(default_factory=list, description="Network signatures")

class DefensiveMeasuresAndRecommendations(BaseModel):
    detection_methods_suggested: List[str] = Field(default_factory=list, description="Detection methods")
    containment_strategies_recommended: List[str] = Field(default_factory=list, description="Containment strategies")
    remediation_strategies_recommended: List[str] = Field(default_factory=list, description="Remediation strategies")
    recovery_strategies_recommended: List[str] = Field(default_factory=list, description="Recovery strategies")
    general_security_recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    prevention_measures: List[str] = Field(default_factory=list, description="Prevention measures")
    monitoring_recommendations: List[str] = Field(default_factory=list, description="Monitoring recommendations")

class ActionableIntelligenceForPlaybooks(BaseModel):
    actionability_level: ActionabilityLevel = Field(..., description="Urgency level")
    solution_category_keywords: List[str] = Field(default_factory=list, description="Solution categories")
    playbook_relevance: List[str] = Field(default_factory=list, description="Relevant playbooks")
    automation_opportunities: List[str] = Field(default_factory=list, description="Automation opportunities")
    integration_points: List[str] = Field(default_factory=list, description="Integration points")
    compliance_relevance: List[str] = Field(default_factory=list, description="Compliance frameworks")

class SourceMetadata(BaseModel):
    source_url: str = Field(..., description="Original article URL")
    source_domain: str = Field(..., description="Source domain")
    source_reputation_score: Optional[float] = Field(None, description="0-1 reputation score")
    author_name: Optional[str] = Field(None, description="Article author")
    publication_date: Optional[str] = Field(None, description="Publication date")
    last_updated: Optional[str] = Field(None, description="Last update date")
    content_length: Optional[int] = Field(None, description="Content length in characters")
    source_category: Optional[str] = Field(None, description="Source category")

class CybersecurityIntelligenceSchema(BaseModel):
    """Complete cybersecurity intelligence extraction schema"""
    ai_analysis_metadata: AIAnalysisMetadata
    source_metadata: SourceMetadata
    article_summary_and_context: ArticleSummaryAndContext
    incident_event_details: IncidentEventDetails
    threat_actor_and_ttps: ThreatActorAndTTPs
    vulnerabilities_and_malware: VulnerabilitiesAndMalware
    indicators_of_compromise: IndicatorsOfCompromise
    defensive_measures_and_recommendations: DefensiveMeasuresAndRecommendations
    actionable_intelligence_for_playbooks: ActionableIntelligenceForPlaybooks

# System prompt for AI analysis
SYSTEM_PROMPT = """You are an expert cybersecurity intelligence analyst AI. Your primary function is to meticulously read cybersecurity articles and extract detailed, structured information according to a precise JSON schema.

You MUST adhere strictly to the JSON structure provided below.
- Your entire response MUST be a single, valid JSON object.
- Do NOT add any fields or keys that are not explicitly defined in the schema.
- Do NOT include any explanatory text, conversation, or markdown formatting before or after the JSON output.
- For any field where information cannot be found in the provided text:
    - Use `null` for optional string, number, or object fields.
    - Use an empty string `""` if a string value is expected but no specific content is found.
    - Use an empty list `[]` for fields expecting a list if no items are found.
- Pay close attention to the expected data types (string, list of strings, object, boolean) and the descriptions provided for each field.
- Be conservative in your analysis - only extract information that is clearly stated or strongly implied in the text.
- For confidence assessments, consider the quality of sources, specificity of details, and corroboration within the text.

The `analysis_timestamp`, `ai_model_used`, and `prompt_version` fields within `ai_analysis_metadata` should be populated based on the context of this interaction.

Extract information according to this JSON schema structure. Focus on accuracy and completeness while maintaining the exact structure provided."""

# Simplified schema for JSON extraction (without Pydantic models)
JSON_SCHEMA = {
    "ai_analysis_metadata": {
        "analysis_timestamp": "string",
        "ai_model_used": "string", 
        "prompt_version": "string",
        "confidence_in_analysis": "High | Medium | Low",
        "is_likely_primary_source": "boolean",
        "processing_time_seconds": "number",
        "extraction_completeness_score": "number"
    },
    "source_metadata": {
        "source_url": "string",
        "source_domain": "string", 
        "source_reputation_score": "number",
        "author_name": "string",
        "publication_date": "string",
        "last_updated": "string",
        "content_length": "number",
        "source_category": "string"
    },
    "article_summary_and_context": {
        "story_summary": "string",
        "post_type": "Incident Report | Threat Actor Profile | Vulnerability Analysis | Malware Deep Dive | Security Advisory | News Brief | Research Paper | Product Review | Threat Landscape Report | Other",
        "tags": ["string"],
        "story_depth": "Overview/Brief | General Technical | Detailed Analysis | Deep Dive/Forensic | Strategic/Executive Summary",
        "target_audience_relevance": ["string"],
        "key_takeaways": ["string"],
        "language_detected": "string",
        "content_quality_score": "number"
    },
    "incident_event_details": {
        "incident_date_approx": "string",
        "disclosure_date_approx": "string", 
        "regions_impacted": ["string"],
        "industry_targeted": ["string"],
        "impact_description": "string",
        "severity_assessment": "Critical | High | Medium | Low | Informational | Not Specified",
        "estimated_financial_impact": "string",
        "affected_user_count": "string",
        "business_disruption_duration": "string"
    },
    "threat_actor_and_ttps": {
        "attacker_group_suspected": ["string"],
        "attacker_motivation": "string",
        "ttps_observed_mitre": ["string"],
        "ttps_observed_descriptive": ["string"],
        "novel_techniques_highlighted": ["string"],
        "attribution_confidence": "High | Medium | Low",
        "campaign_names": ["string"],
        "infrastructure_details": ["string"]
    },
    "vulnerabilities_and_malware": {
        "vulnerabilities_exploited_desc": ["string"],
        "cve_ids_mentioned": ["string"],
        "malware_families_involved": ["string"],
        "targeted_technologies_platforms": ["string"],
        "exploit_availability": "string",
        "patch_availability": "string",
        "zero_day_indicators": ["string"]
    },
    "indicators_of_compromise": {
        "ips": ["string"],
        "domains": ["string"],
        "urls": ["string"],
        "hashes": {
            "md5": ["string"],
            "sha1": ["string"],
            "sha256": ["string"],
            "sha512": ["string"]
        },
        "email_addresses": ["string"],
        "file_names": ["string"],
        "registry_keys": ["string"],
        "mutexes": ["string"],
        "other_iocs_desc": ["string"],
        "yara_rules": ["string"],
        "network_signatures": ["string"]
    },
    "defensive_measures_and_recommendations": {
        "detection_methods_suggested": ["string"],
        "containment_strategies_recommended": ["string"],
        "remediation_strategies_recommended": ["string"],
        "recovery_strategies_recommended": ["string"],
        "general_security_recommendations": ["string"],
        "prevention_measures": ["string"],
        "monitoring_recommendations": ["string"]
    },
    "actionable_intelligence_for_playbooks": {
        "actionability_level": "Immediate Action Required | High Priority Awareness | Operational Review | Informational/Contextual | Strategic Consideration",
        "solution_category_keywords": ["string"],
        "playbook_relevance": ["string"],
        "automation_opportunities": ["string"],
        "integration_points": ["string"],
        "compliance_relevance": ["string"]
    }
}