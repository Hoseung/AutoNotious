from notion_client import Client
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class NotionWriter:
    def __init__(self, api_key: str, parent_page_id: str):
        self.client = Client(auth=api_key)
        self.parent_page_id = parent_page_id
    
    def markdown_to_notion_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        blocks = []
        lines = markdown.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            if not line:
                i += 1
                continue
            
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            
            elif line.startswith('- '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self.parse_inline_formatting(line[2:])
                    }
                })
            
            elif line.startswith('```'):
                code_lines = []
                language = line[3:].strip() or "plain text"
                i += 1
                
                while i < len(lines) and not lines[i].rstrip().startswith('```'):
                    code_lines.append(lines[i].rstrip())
                    i += 1
                
                if code_lines:
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_lines)}}],
                            "language": "plain text"
                        }
                    })
            
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self.parse_inline_formatting(line)
                    }
                })
            
            i += 1
        
        return blocks
    
    def parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        rich_text = []
        
        bold_pattern = r'\*\*(.*?)\*\*'
        code_pattern = r'`([^`]+)`'
        
        combined_pattern = f'({bold_pattern}|{code_pattern})'
        
        parts = re.split(combined_pattern, text)
        
        i = 0
        while i < len(parts):
            part = parts[i] if parts[i] else ""
            
            if not part:
                i += 1
                continue
            
            if i + 2 < len(parts) and parts[i] == '**' and parts[i + 2] == '**':
                rich_text.append({
                    "type": "text",
                    "text": {"content": parts[i + 1]},
                    "annotations": {"bold": True}
                })
                i += 3
            elif part.startswith('**') and part.endswith('**') and len(part) > 4:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[2:-2]},
                    "annotations": {"bold": True}
                })
                i += 1
            elif part.startswith('`') and part.endswith('`') and len(part) > 2:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[1:-1]},
                    "annotations": {"code": True}
                })
                i += 1
            else:
                if part:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": part}
                    })
                i += 1
        
        if not rich_text:
            rich_text = [{"type": "text", "text": {"content": text}}]
        
        return rich_text
    
    async def create_notion_page(
        self, 
        title: str, 
        markdown_content: str
    ) -> Dict[str, str]:
        try:
            blocks = self.markdown_to_notion_blocks(markdown_content)
            
            page = self.client.pages.create(
                parent={"page_id": self.parent_page_id},
                properties={
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                },
                children=blocks[:100]
            )
            
            page_id = page["id"]
            page_url = page["url"]
            
            if len(blocks) > 100:
                for i in range(100, len(blocks), 100):
                    batch = blocks[i:i+100]
                    self.client.blocks.children.append(
                        block_id=page_id,
                        children=batch
                    )
            
            logger.info(f"Created Notion page: {page_id}")
            
            return {
                "page_id": page_id,
                "url": page_url
            }
            
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise
    
    def validate_config(self) -> bool:
        try:
            self.client.pages.retrieve(page_id=self.parent_page_id)
            return True
        except Exception as e:
            logger.error(f"Invalid Notion configuration: {e}")
            return False