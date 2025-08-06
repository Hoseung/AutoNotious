import pytest
from unittest.mock import MagicMock, patch
from app.services.notion_writer import NotionWriter


class TestNotionWriter:
    @pytest.fixture
    def notion_writer(self):
        return NotionWriter("test_api_key", "test_parent_id")
    
    def test_parse_inline_formatting_bold(self, notion_writer):
        text = "This is **bold** text"
        result = notion_writer.parse_inline_formatting(text)
        
        assert len(result) == 3
        assert result[0]["text"]["content"] == "This is "
        assert result[1]["text"]["content"] == "bold"
        assert result[1].get("annotations", {}).get("bold") == True
        assert result[2]["text"]["content"] == " text"
    
    def test_parse_inline_formatting_code(self, notion_writer):
        text = "This is `code` text"
        result = notion_writer.parse_inline_formatting(text)
        
        assert len(result) == 3
        assert result[0]["text"]["content"] == "This is "
        assert result[1]["text"]["content"] == "code"
        assert result[1].get("annotations", {}).get("code") == True
        assert result[2]["text"]["content"] == " text"
    
    def test_parse_inline_formatting_mixed(self, notion_writer):
        text = "**Bold** and `code` together"
        result = notion_writer.parse_inline_formatting(text)
        
        assert any(r.get("annotations", {}).get("bold") for r in result)
        assert any(r.get("annotations", {}).get("code") for r in result)
    
    def test_markdown_to_notion_blocks_heading1(self, notion_writer):
        markdown = "# Main Title"
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_1"
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Main Title"
    
    def test_markdown_to_notion_blocks_heading2(self, notion_writer):
        markdown = "## Subtitle"
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Subtitle"
    
    def test_markdown_to_notion_blocks_bullet(self, notion_writer):
        markdown = "- Item 1\n- Item 2"
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 2
        assert all(b["type"] == "bulleted_list_item" for b in blocks)
        assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Item 1"
        assert blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Item 2"
    
    def test_markdown_to_notion_blocks_code(self, notion_writer):
        markdown = "```python\nprint('hello')\n```"
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "code"
        assert blocks[0]["code"]["rich_text"][0]["text"]["content"] == "print('hello')"
    
    def test_markdown_to_notion_blocks_paragraph(self, notion_writer):
        markdown = "Regular paragraph text"
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "Regular paragraph text"
    
    def test_markdown_to_notion_blocks_mixed(self, notion_writer):
        markdown = """# Title

## Section

- Bullet point
- Another bullet

Regular paragraph

```
code block
```"""
        
        blocks = notion_writer.markdown_to_notion_blocks(markdown)
        
        block_types = [b["type"] for b in blocks]
        assert "heading_1" in block_types
        assert "heading_2" in block_types
        assert "bulleted_list_item" in block_types
        assert "paragraph" in block_types
        assert "code" in block_types
    
    @pytest.mark.asyncio
    async def test_create_notion_page(self, notion_writer):
        with patch.object(notion_writer.client.pages, 'create') as mock_create:
            with patch.object(notion_writer.client.blocks.children, 'append') as mock_append:
                mock_create.return_value = {
                    "id": "test_page_id",
                    "url": "https://notion.so/test_page"
                }
                
                title = "Test Page"
                markdown = "# Test\n\nContent"
                
                result = await notion_writer.create_notion_page(title, markdown)
                
                assert result["page_id"] == "test_page_id"
                assert result["url"] == "https://notion.so/test_page"
                mock_create.assert_called_once()
    
    def test_validate_config_success(self, notion_writer):
        with patch.object(notion_writer.client.pages, 'retrieve') as mock_retrieve:
            mock_retrieve.return_value = {"id": "test_parent_id"}
            
            assert notion_writer.validate_config() == True
    
    def test_validate_config_failure(self, notion_writer):
        with patch.object(notion_writer.client.pages, 'retrieve') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Not found")
            
            assert notion_writer.validate_config() == False