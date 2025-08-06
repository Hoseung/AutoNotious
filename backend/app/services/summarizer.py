from typing import List, Dict, Tuple
from .llm_service import LLMService
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class SummarizerService:
    def __init__(self):
        self.llm_service = LLMService()
        
    async def __aenter__(self):
        await self.llm_service.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.llm_service.__aexit__(exc_type, exc_val, exc_tb)
    
    def chunk_messages(
        self, 
        messages: List[Dict[str, str]], 
        chunk_size: int = 3000
    ) -> List[List[Dict[str, str]]]:
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for msg in messages:
            msg_tokens = self.llm_service.count_tokens(msg["content"])
            
            if current_tokens + msg_tokens > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(msg)
            current_tokens += msg_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def format_chunk_for_summary(self, messages: List[Dict[str, str]]) -> str:
        formatted = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n\n".join(formatted)
    
    async def summarize_chunk(self, chunk_text: str) -> str:
        prompt = f"""Summarize the following conversation chunk concisely, preserving key points, action items, and important details:

{chunk_text}

Provide a structured summary with:
- Main topics discussed
- Key decisions or conclusions
- Action items (if any)
- Important technical details or code snippets"""
        
        messages = [{"role": "user", "content": prompt}]
        
        return await self.llm_service.get_completion(
            messages,
            temperature=settings.summary_temperature,
            top_p=settings.summary_top_p
        )
    
    async def combine_summaries(self, summaries: List[str], title: str) -> str:
        combined = "\n\n---\n\n".join(summaries)
        
        prompt = f"""Based on these conversation summaries, create a final structured markdown document.

Title suggestion: {title}

Summaries:
{combined}

Create a markdown document with EXACTLY these sections (all sections must be present even if empty):

# [Title - max 80 characters]

## TL;DR
[1-2 bullet points summarizing the entire conversation]

## Key Points
[Main discussion points as bullet list]

## Action Items
[Bullet list of action items. Include "Owner:" and "Due:" ONLY if explicitly mentioned in the conversation]

## Notes
[Any important links, code snippets, or additional context]

Requirements:
- Use only basic Markdown: #, ##, -, **bold**, `code`
- Be faithful to the source material
- Do not add information not present in the conversation
- Keep sections even if they would be empty (use "None" or "N/A" if needed)"""
        
        messages = [{"role": "user", "content": prompt}]
        
        return await self.llm_service.get_completion(
            messages,
            temperature=settings.summary_temperature,
            top_p=settings.summary_top_p
        )
    
    async def summarize_session(
        self, 
        messages: List[Dict[str, str]]
    ) -> Tuple[str, str]:
        if not messages:
            return "Empty Session", "# Empty Session\n\n## TL;DR\n- No messages in session\n\n## Key Points\n- N/A\n\n## Action Items\n- N/A\n\n## Notes\n- N/A"
        
        title = self.generate_title(messages)
        
        if len(messages) <= 10:
            chunk_text = self.format_chunk_for_summary(messages)
            summary = await self.summarize_chunk(chunk_text)
            final_markdown = await self.combine_summaries([summary], title)
        else:
            chunks = self.chunk_messages(messages)
            summaries = []
            
            for chunk in chunks:
                chunk_text = self.format_chunk_for_summary(chunk)
                summary = await self.summarize_chunk(chunk_text)
                summaries.append(summary)
            
            final_markdown = await self.combine_summaries(summaries, title)
        
        extracted_title = self.extract_title_from_markdown(final_markdown)
        
        return extracted_title or title, final_markdown
    
    def generate_title(self, messages: List[Dict[str, str]]) -> str:
        first_user_msg = next(
            (msg["content"] for msg in messages if msg["role"] == "user"),
            "Chat Session"
        )
        
        title = first_user_msg[:77] + "..." if len(first_user_msg) > 80 else first_user_msg
        return title.replace("\n", " ").strip()
    
    def extract_title_from_markdown(self, markdown: str) -> str:
        lines = markdown.split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()[:80]
        return "Chat Session"