import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.summarizer import SummarizerService


class TestSummarizerService:
    @pytest.fixture
    def summarizer(self):
        return SummarizerService()
    
    def test_chunk_messages(self, summarizer):
        messages = [
            {"role": "user", "content": "Short message"},
            {"role": "assistant", "content": "Short reply"},
            {"role": "user", "content": "Another message"},
            {"role": "assistant", "content": "Another reply"},
            {"role": "user", "content": "A much longer message that contains more tokens"},
            {"role": "assistant", "content": "A much longer reply with many words"},
        ]
        
        chunks = summarizer.chunk_messages(messages, chunk_size=50)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, list) for chunk in chunks)
        
        all_messages = []
        for chunk in chunks:
            all_messages.extend(chunk)
        assert len(all_messages) == len(messages)
    
    def test_format_chunk_for_summary(self, summarizer):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        formatted = summarizer.format_chunk_for_summary(messages)
        
        assert "User: Hello" in formatted
        assert "Assistant: Hi there!" in formatted
        assert formatted.count("\n\n") == 1
    
    def test_generate_title(self, summarizer):
        messages = [
            {"role": "user", "content": "How do I implement a binary search tree?"},
            {"role": "assistant", "content": "To implement a binary search tree..."},
        ]
        
        title = summarizer.generate_title(messages)
        
        assert title == "How do I implement a binary search tree?"
        assert len(title) <= 80
    
    def test_generate_title_truncation(self, summarizer):
        long_message = "x" * 100
        messages = [{"role": "user", "content": long_message}]
        
        title = summarizer.generate_title(messages)
        
        assert len(title) == 80
        assert title.endswith("...")
    
    def test_extract_title_from_markdown(self, summarizer):
        markdown = """# Test Title

## TL;DR
- Summary point

## Key Points
- Point 1"""
        
        title = summarizer.extract_title_from_markdown(markdown)
        assert title == "Test Title"
    
    @pytest.mark.asyncio
    async def test_summarize_chunk(self, summarizer):
        with patch.object(summarizer.llm_service, 'get_completion') as mock_completion:
            mock_completion.return_value = "Summary of the chunk"
            
            chunk_text = "User: Test\n\nAssistant: Response"
            result = await summarizer.summarize_chunk(chunk_text)
            
            assert result == "Summary of the chunk"
            mock_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_combine_summaries(self, summarizer):
        with patch.object(summarizer.llm_service, 'get_completion') as mock_completion:
            mock_completion.return_value = """# Combined Summary

## TL;DR
- Main point

## Key Points
- Detail 1

## Action Items
- Task 1

## Notes
- Note 1"""
            
            summaries = ["Summary 1", "Summary 2"]
            title = "Test Title"
            
            result = await summarizer.combine_summaries(summaries, title)
            
            assert "# Combined Summary" in result
            assert "## TL;DR" in result
            assert "## Key Points" in result
            assert "## Action Items" in result
            assert "## Notes" in result
    
    @pytest.mark.asyncio
    async def test_summarize_session_empty(self, summarizer):
        title, markdown = await summarizer.summarize_session([])
        
        assert title == "Empty Session"
        assert "# Empty Session" in markdown
        assert "N/A" in markdown