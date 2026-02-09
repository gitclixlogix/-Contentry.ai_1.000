"""
Multi-Agent System for Content Generation and Analysis

This module provides a true multi-agent architecture where specialized agents
collaborate to produce high-quality, compliant, culturally-sensitive content
and perform comprehensive content analysis.

CONTENT GENERATION AGENTS:
    Orchestrator Agent
        ├── Research Agent (news, trends, data gathering)
        ├── Writer Agent (content creation, tone matching)
        ├── Compliance Agent (policy, legal, brand checks)
        └── Cultural Agent (global sensitivity analysis)

CONTENT ANALYSIS AGENTS:
    Analysis Orchestrator
        ├── Visual Agent (image/video frame analysis)
        ├── Text Agent (sentiment, tone, claims)
        ├── Compliance Agent (policy checking)
        └── Risk Assessment Agent (final risk scoring)

Each agent:
- Has its own expertise and system prompt
- Can use tools autonomously
- Communicates via structured messages
- Makes independent decisions within its domain
"""

from .base_agent import BaseAgent, AgentMessage, AgentRole, Tool

# Content Generation Agents
from .orchestrator_agent import OrchestratorAgent
from .research_agent import ResearchAgent
from .writer_agent import WriterAgent
from .compliance_agent import ComplianceAgent
from .cultural_agent import CulturalAgent

# Content Analysis Agents
from .analysis_orchestrator import AnalysisOrchestratorAgent, AnalysisContext
from .visual_agent import VisualAnalysisAgent
from .text_agent import TextAnalysisAgent
from .risk_agent import RiskAssessmentAgent

__all__ = [
    # Base
    'BaseAgent',
    'AgentMessage', 
    'AgentRole',
    'Tool',
    
    # Content Generation
    'OrchestratorAgent',
    'ResearchAgent',
    'WriterAgent',
    'ComplianceAgent',
    'CulturalAgent',
    
    # Content Analysis
    'AnalysisOrchestratorAgent',
    'AnalysisContext',
    'VisualAnalysisAgent',
    'TextAnalysisAgent',
    'RiskAssessmentAgent',
]
