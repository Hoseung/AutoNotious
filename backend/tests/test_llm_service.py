import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_service import LLMService


class TestLLMService:
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    def test_count_tokens(self, llm_service):
        text = "Hello, this is a test message."
        token_count = llm_service.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_trim_messages_to_token_limit(self, llm_service):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
        ]
        
        trimmed = llm_service.trim_messages_to_token_limit(messages, max_tokens=50)
        
        assert len(trimmed) <= len(messages)
        assert all(msg in messages for msg in trimmed)
        
        total_tokens = sum(
            llm_service.count_tokens(msg["content"]) 
            for msg in trimmed
        )
        assert total_tokens <= 50
    
    @pytest.mark.asyncio
    async def test_stream_chat_completion(self, llm_service):
        with patch.object(llm_service.client, 'stream') as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines = AsyncMock(return_value=[
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"delta":{"content":" world"}}]}',
                'data: [DONE]'
            ].__aiter__())
            mock_response.raise_for_status = MagicMock()
            
            mock_stream.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "Hi"}]
            chunks = []
            
            async for chunk in llm_service.stream_chat_completion(messages):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " world"]
    
    @pytest.mark.asyncio
    async def test_get_completion(self, llm_service):
        with patch.object(llm_service.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json = MagicMock(return_value={
                "choices": [{"message": {"content": "Test response"}}]
            })
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            messages = [{"role": "user", "content": "Test"}]
            result = await llm_service.get_completion(messages)
            
            assert result == "Test response"