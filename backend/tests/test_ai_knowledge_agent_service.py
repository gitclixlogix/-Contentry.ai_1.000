"""
Unit Tests for AI Knowledge Agent Service

Tests document and image analysis for knowledge extraction:
- Document text extraction (PDF, DOCX, TXT)
- Rule extraction from text using LLM
- Image color extraction
- Visual theme extraction
- Knowledge base storage
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64

from services.ai_knowledge_agent import (
    AIKnowledgeAgentService,
    get_knowledge_agent,
    init_knowledge_agent
)


@pytest.fixture
def mock_db():
    """Create mock database"""
    db = MagicMock()
    db.knowledge_documents = MagicMock()
    db.knowledge_documents.insert_one = AsyncMock()
    return db


@pytest.fixture
def knowledge_agent(mock_db):
    """Create AIKnowledgeAgentService instance"""
    with patch.dict('os.environ', {'EMERGENT_LLM_KEY': 'test_key'}):
        return AIKnowledgeAgentService(mock_db)


@pytest.fixture
def knowledge_agent_no_llm(mock_db):
    """Create AIKnowledgeAgentService without LLM key"""
    with patch.dict('os.environ', {}, clear=True):
        return AIKnowledgeAgentService(mock_db)


class TestAIKnowledgeAgentInit:
    """Test AIKnowledgeAgentService initialization"""
    
    def test_agent_initializes_with_db(self, mock_db):
        """Test agent stores db reference"""
        agent = AIKnowledgeAgentService(mock_db)
        assert agent.db == mock_db
    
    def test_agent_initializes_llm_key(self):
        """Test agent initializes with LLM key"""
        mock_db = MagicMock()
        with patch.dict('os.environ', {'EMERGENT_LLM_KEY': 'test_key'}):
            agent = AIKnowledgeAgentService(mock_db)
            assert agent.llm_key == 'test_key'
    
    def test_agent_handles_missing_llm_key(self):
        """Test agent handles missing LLM key gracefully"""
        mock_db = MagicMock()
        with patch.dict('os.environ', {}, clear=True):
            agent = AIKnowledgeAgentService(mock_db)
            assert agent.llm_key is None


class TestGlobalAgentManagement:
    """Test global agent instance management"""
    
    def test_get_knowledge_agent_raises_when_not_initialized(self):
        """Test get_knowledge_agent raises before init"""
        # Reset global
        with patch('services.ai_knowledge_agent._knowledge_agent', None):
            with pytest.raises(RuntimeError) as exc_info:
                get_knowledge_agent()
            assert "not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_init_knowledge_agent_creates_instance(self, mock_db):
        """Test init_knowledge_agent creates global instance"""
        with patch('services.ai_knowledge_agent._knowledge_agent', None):
            result = await init_knowledge_agent(mock_db)
            assert isinstance(result, AIKnowledgeAgentService)


class TestAnalyzeDocument:
    """Test document analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_document_txt(self, knowledge_agent):
        """Test analyzing text document"""
        content = b"Brand voice should be professional. Never use slang. Always capitalize Product Names."
        
        mock_rules = [
            {"rule": "Brand voice should be professional", "category": "voice", "priority": "high"},
            {"rule": "Never use slang", "category": "prohibited", "priority": "medium"}
        ]
        
        with patch.object(knowledge_agent, '_extract_rules_from_text', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_rules
            
            result = await knowledge_agent.analyze_document(
                file_content=content,
                file_name="brand_guidelines.txt",
                mime_type="text/plain",
                profile_id="profile_123"
            )
        
        assert result["success"] == True
        assert result["source_type"] == "document"
        assert result["rule_count"] == 2
    
    @pytest.mark.asyncio
    async def test_analyze_document_insufficient_text(self, knowledge_agent):
        """Test analyzing document with too little text"""
        content = b"Short"
        
        result = await knowledge_agent.analyze_document(
            file_content=content,
            file_name="short.txt",
            mime_type="text/plain",
            profile_id="profile_123"
        )
        
        assert result["success"] == False
        assert "Could not extract sufficient text" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_document_handles_error(self, knowledge_agent):
        """Test document analysis error handling"""
        with patch.object(knowledge_agent, '_extract_document_text', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")
            
            result = await knowledge_agent.analyze_document(
                file_content=b"test",
                file_name="test.txt",
                mime_type="text/plain",
                profile_id="profile_123"
            )
        
        assert result["success"] == False
        assert "error" in result


class TestExtractDocumentText:
    """Test text extraction from documents"""
    
    @pytest.mark.asyncio
    async def test_extract_text_plain(self, knowledge_agent):
        """Test extracting text from plain text file"""
        content = b"This is plain text content."
        
        result = await knowledge_agent._extract_document_text(
            file_content=content,
            file_name="test.txt",
            mime_type="text/plain"
        )
        
        assert result == "This is plain text content."
    
    @pytest.mark.asyncio
    async def test_extract_text_markdown(self, knowledge_agent):
        """Test extracting text from markdown file"""
        content = b"# Heading\n\nThis is markdown content."
        
        result = await knowledge_agent._extract_document_text(
            file_content=content,
            file_name="test.md",
            mime_type="text/markdown"
        )
        
        assert "# Heading" in result
        assert "markdown content" in result
    
    @pytest.mark.asyncio
    async def test_extract_text_generic(self, knowledge_agent):
        """Test extracting text from unknown file type falls back to text"""
        content = b"Generic text content here."
        
        result = await knowledge_agent._extract_document_text(
            file_content=content,
            file_name="test.unknown",
            mime_type="application/octet-stream"
        )
        
        assert "Generic text content" in result


class TestExtractRulesFromText:
    """Test rule extraction from text"""
    
    @pytest.mark.asyncio
    async def test_extract_rules_fallback(self, knowledge_agent_no_llm):
        """Test rule extraction fallback without LLM"""
        text = "Always use professional tone. Never use slang words in communications."
        
        result = await knowledge_agent_no_llm._extract_rules_from_text(text, "profile_123")
        
        # Should return basic extraction results
        assert isinstance(result, list)


class TestBasicRuleExtraction:
    """Test basic keyword-based rule extraction"""
    
    def test_basic_extraction_required_rules(self, knowledge_agent):
        """Test extracting required rules"""
        text = "You must always include trademark symbol after brand names. Required to capitalize all product names."
        
        result = knowledge_agent._basic_rule_extraction(text)
        
        assert len(result) > 0
        required_rules = [r for r in result if r["category"] == "required"]
        assert len(required_rules) > 0
    
    def test_basic_extraction_prohibited_rules(self, knowledge_agent):
        """Test extracting prohibited rules"""
        text = "Never mention competitor names. Don't use slang in official content. Avoid negative language."
        
        result = knowledge_agent._basic_rule_extraction(text)
        
        prohibited_rules = [r for r in result if r["category"] == "prohibited"]
        assert len(prohibited_rules) > 0
    
    def test_basic_extraction_limits_results(self, knowledge_agent):
        """Test extraction limits to 10 rules"""
        # Create text with many rules
        text = " ".join([f"Always do thing {i}. Never do bad thing {i}." for i in range(20)])
        
        result = knowledge_agent._basic_rule_extraction(text)
        
        assert len(result) <= 10


class TestAnalyzeImage:
    """Test image analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, knowledge_agent):
        """Test successful image analysis"""
        image_content = b"fake_image_content"
        
        mock_colors = [
            {"hex": "#FF5733", "name": "Orange", "score": 50},
            {"hex": "#333333", "name": "Gray", "score": 30}
        ]
        
        mock_analysis = {
            "labels": [{"description": "Logo"}],
            "detected_text": "Brand Name"
        }
        
        mock_rules = [
            {"rule": "Primary color: Orange", "category": "colors", "priority": "high"}
        ]
        
        with patch.object(knowledge_agent, '_extract_colors_from_image', new_callable=AsyncMock) as mock_colors_fn, \
             patch.object(knowledge_agent, '_analyze_image_content', new_callable=AsyncMock) as mock_analyze, \
             patch.object(knowledge_agent, '_extract_visual_rules', new_callable=AsyncMock) as mock_rules_fn:
            
            mock_colors_fn.return_value = mock_colors
            mock_analyze.return_value = mock_analysis
            mock_rules_fn.return_value = mock_rules
            
            result = await knowledge_agent.analyze_image(
                image_content=image_content,
                file_name="logo.png",
                mime_type="image/png",
                profile_id="profile_123"
            )
        
        assert result["success"] == True
        assert result["source_type"] == "image"
        assert len(result["colors"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_image_handles_error(self, knowledge_agent):
        """Test image analysis error handling"""
        with patch.object(knowledge_agent, '_extract_colors_from_image', new_callable=AsyncMock) as mock_colors:
            mock_colors.side_effect = Exception("Color extraction failed")
            
            result = await knowledge_agent.analyze_image(
                image_content=b"test",
                file_name="test.png",
                mime_type="image/png",
                profile_id="profile_123"
            )
        
        assert result["success"] == False
        assert "error" in result


class TestGetColorName:
    """Test color name determination"""
    
    def test_get_color_name_white(self, knowledge_agent):
        """Test white color detection"""
        result = knowledge_agent._get_color_name(255, 255, 255)
        assert result == "White"
    
    def test_get_color_name_black(self, knowledge_agent):
        """Test black color detection"""
        result = knowledge_agent._get_color_name(0, 0, 0)
        assert result == "Black"
    
    def test_get_color_name_red(self, knowledge_agent):
        """Test red color detection"""
        result = knowledge_agent._get_color_name(255, 50, 50)
        assert result == "Red"
    
    def test_get_color_name_green(self, knowledge_agent):
        """Test green color detection"""
        result = knowledge_agent._get_color_name(50, 255, 50)
        assert result == "Green"
    
    def test_get_color_name_blue(self, knowledge_agent):
        """Test blue color detection"""
        result = knowledge_agent._get_color_name(50, 50, 255)
        assert result == "Blue"
    
    def test_get_color_name_yellow(self, knowledge_agent):
        """Test yellow color detection"""
        result = knowledge_agent._get_color_name(255, 255, 50)
        assert result == "Yellow"
    
    def test_get_color_name_orange(self, knowledge_agent):
        """Test orange color detection"""
        result = knowledge_agent._get_color_name(255, 165, 50)
        assert result == "Orange"
    
    def test_get_color_name_purple(self, knowledge_agent):
        """Test purple color detection"""
        result = knowledge_agent._get_color_name(160, 50, 160)
        assert result == "Purple"
    
    def test_get_color_name_custom(self, knowledge_agent):
        """Test custom color fallback"""
        result = knowledge_agent._get_color_name(128, 64, 192)
        # Should return Custom or some color name
        assert isinstance(result, str)


class TestAnalyzeImageContent:
    """Test image content analysis with Vision API"""
    
    @pytest.mark.asyncio
    async def test_analyze_image_content_returns_empty_on_unavailable(self, knowledge_agent):
        """Test image analysis returns empty when Vision API unavailable"""
        # Test that the method handles missing vision service gracefully
        result = await knowledge_agent._analyze_image_content(b"image", "image/png")
        
        # Should return empty default structure
        assert isinstance(result, dict)
        assert "labels" in result
        assert "detected_text" in result


class TestExtractVisualRules:
    """Test visual rule extraction"""
    
    @pytest.mark.asyncio
    async def test_extract_visual_rules_colors(self, knowledge_agent):
        """Test visual rules include color rules"""
        colors = [
            {"name": "Blue", "hex": "#0000FF"},
            {"name": "White", "hex": "#FFFFFF"}
        ]
        
        result = await knowledge_agent._extract_visual_rules(
            colors=colors,
            labels=[],
            detected_text="",
            file_name="logo.png"
        )
        
        # Should have color rules
        color_rules = [r for r in result if r["category"] == "colors"]
        assert len(color_rules) > 0
        assert "Blue" in color_rules[0]["rule"]
    
    @pytest.mark.asyncio
    async def test_extract_visual_rules_empty_colors(self, knowledge_agent):
        """Test visual rules with no colors"""
        result = await knowledge_agent._extract_visual_rules(
            colors=[],
            labels=[],
            detected_text="",
            file_name="empty.png"
        )
        
        # Should return empty or minimal rules
        assert isinstance(result, list)


class TestFormatRulesAsSummary:
    """Test rule formatting as summary"""
    
    def test_format_empty_rules(self, knowledge_agent):
        """Test formatting empty rules"""
        result = knowledge_agent._format_rules_as_summary([], "document", "test.txt")
        assert "No specific rules" in result
    
    def test_format_rules_by_category(self, knowledge_agent):
        """Test rules are grouped by category"""
        rules = [
            {"rule": "Be professional", "category": "voice", "priority": "high"},
            {"rule": "No slang", "category": "prohibited", "priority": "medium"},
            {"rule": "Use trademark", "category": "required", "priority": "high"}
        ]
        
        result = knowledge_agent._format_rules_as_summary(rules, "document", "guidelines.pdf")
        
        assert "Brand Voice" in result
        assert "Prohibited" in result
        assert "Required" in result
    
    def test_format_includes_priority_icons(self, knowledge_agent):
        """Test summary includes priority indicators"""
        rules = [
            {"rule": "High priority rule", "category": "voice", "priority": "high"},
            {"rule": "Medium priority rule", "category": "voice", "priority": "medium"}
        ]
        
        result = knowledge_agent._format_rules_as_summary(rules, "document", "test.txt")
        
        # Should contain priority indicators
        assert "🔴" in result or "🟡" in result


class TestSaveToKnowledgeBase:
    """Test saving to knowledge base"""
    
    @pytest.mark.asyncio
    async def test_save_to_knowledge_base_success(self, knowledge_agent, mock_db):
        """Test successful save to knowledge base"""
        rules = [
            {"rule": "Test rule", "category": "voice", "priority": "high"}
        ]
        
        result = await knowledge_agent.save_to_knowledge_base(
            profile_id="profile_123",
            user_id="user_123",
            summary="## Extracted Rules",
            source_file="guidelines.pdf",
            extracted_rules=rules
        )
        
        assert result["success"] == True
        assert result["rule_count"] == 1
        mock_db.knowledge_documents.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_to_knowledge_base_creates_document(self, knowledge_agent, mock_db):
        """Test knowledge document is created correctly"""
        rules = [{"rule": "Test", "category": "voice", "priority": "high"}]
        
        await knowledge_agent.save_to_knowledge_base(
            profile_id="profile_123",
            user_id="user_123",
            summary="Summary",
            source_file="test.pdf",
            extracted_rules=rules
        )
        
        call_args = mock_db.knowledge_documents.insert_one.call_args[0][0]
        assert call_args["profile_id"] == "profile_123"
        assert call_args["user_id"] == "user_123"
        assert call_args["tier"] == "profile"
        assert call_args["extraction_method"] == "ai_knowledge_agent"
    
    @pytest.mark.asyncio
    async def test_save_to_knowledge_base_handles_error(self, knowledge_agent, mock_db):
        """Test error handling when saving fails"""
        mock_db.knowledge_documents.insert_one.side_effect = Exception("DB Error")
        
        result = await knowledge_agent.save_to_knowledge_base(
            profile_id="profile_123",
            user_id="user_123",
            summary="Summary",
            source_file="test.pdf",
            extracted_rules=[]
        )
        
        assert result["success"] == False
        assert "error" in result
