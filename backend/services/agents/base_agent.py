"""
Base Agent Class

Provides the foundation for all specialized agents in the multi-agent system.
Each agent has:
- A role and expertise area
- Tools it can use
- Ability to reason and make decisions
- Communication with other agents
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timezone
from enum import Enum
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles for agents in the system"""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    WRITER = "writer"
    COMPLIANCE = "compliance"
    CULTURAL = "cultural"
    SEO = "seo"


@dataclass
class Tool:
    """Represents a tool that an agent can use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    
    def to_openai_format(self) -> Dict:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: AgentRole
    to_agent: AgentRole
    content: Any
    message_type: str  # "request", "response", "feedback"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Shared context available to all agents"""
    user_id: str
    original_prompt: str
    language: str = "en"
    tone: str = "professional"
    platforms: List[str] = field(default_factory=list)
    hashtag_count: int = 3
    profile_data: Dict[str, Any] = field(default_factory=dict)
    policies: List[Dict] = field(default_factory=list)
    
    # Accumulated data from agents
    research_data: Dict[str, Any] = field(default_factory=dict)
    draft_content: str = ""
    compliance_feedback: Dict[str, Any] = field(default_factory=dict)
    cultural_feedback: Dict[str, Any] = field(default_factory=dict)
    
    # Message history
    messages: List[AgentMessage] = field(default_factory=list)
    
    # Additional metadata for agents (e.g., target_region, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    
    Each agent:
    - Has a specific role and expertise
    - Can use tools to accomplish tasks
    - Reasons about its domain autonomously
    - Communicates via structured messages
    """
    
    def __init__(
        self,
        role: AgentRole,
        name: str,
        expertise: str,
        model: str = "gpt-4.1-mini"
    ):
        self.role = role
        self.name = name
        self.expertise = expertise
        self.model = model
        self.tools: List[Tool] = []
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the agent's system prompt based on its role"""
        base_prompt = f"""You are {self.name}, a specialized AI agent in a multi-agent content generation system.

YOUR ROLE: {self.role.value.upper()}
YOUR EXPERTISE: {self.expertise}

You are part of a collaborative team of agents:
- Orchestrator: Plans and coordinates the workflow
- Research Agent: Gathers news, trends, and relevant data
- Writer Agent: Creates content drafts
- Compliance Agent: Ensures policy and legal compliance
- Cultural Agent: Ensures global cultural sensitivity

IMPORTANT GUIDELINES:
1. Focus ONLY on your area of expertise
2. Provide structured, actionable output
3. Be concise but thorough
4. Flag any concerns for other agents to address
5. Always explain your reasoning

{self._get_role_specific_prompt()}
"""
        return base_prompt
    
    @abstractmethod
    def _get_role_specific_prompt(self) -> str:
        """Override to add role-specific instructions"""
        pass
    
    def register_tool(self, tool: Tool):
        """Register a tool for this agent to use"""
        self.tools.append(tool)
        logger.debug(f"[{self.name}] Registered tool: {tool.name}")
    
    async def _call_llm(
        self, 
        prompt: str, 
        use_tools: bool = False,
        json_response: bool = False
    ) -> str:
        """Make an LLM call with optional tool use"""
        session_id = f"{self.role.value}_{datetime.now(timezone.utc).timestamp()}"
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self.system_prompt
        ).with_model("openai", self.model)
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return response.strip()
    
    async def _use_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool"""
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        logger.info(f"[{self.name}] Using tool: {tool_name}")
        result = await tool.handler(**kwargs)
        logger.info(f"[{self.name}] Tool {tool_name} completed")
        
        return result
    
    def send_message(self, to_agent: AgentRole, content: Any, message_type: str = "response") -> AgentMessage:
        """Create a message to send to another agent"""
        return AgentMessage(
            from_agent=self.role,
            to_agent=to_agent,
            content=content,
            message_type=message_type
        )
    
    @abstractmethod
    async def execute(self, context: AgentContext, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        Args:
            context: Shared context with accumulated data
            task: Specific task parameters from orchestrator
            
        Returns:
            Result dictionary with agent's output
        """
        pass
    
    def _parse_json_response(self, response: str) -> Dict:
        """Safely parse JSON from LLM response"""
        # Clean markdown code blocks
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.name}] Failed to parse JSON: {e}")
            return {"error": "Failed to parse response", "raw": response}
