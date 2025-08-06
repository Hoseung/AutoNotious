from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session as SQLSession, select
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import AsyncGenerator
import logging
import json

from ..database import get_session
from ..models import Session, Message
from ..services import LLMService
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    session_id: str
    text: str


async def generate_sse_events(
    session_id: str,
    user_message: str,
    db: SQLSession
) -> AsyncGenerator[str, None]:
    try:
        session = db.get(Session, session_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return
        
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()
        
        if not session.title:
            session.title = user_message[:77] + "..." if len(user_message) > 80 else user_message
            db.commit()
        
        statement = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at)
        
        messages = db.exec(statement).all()
        
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        full_response = ""
        
        async with LLMService() as llm_service:
            async for chunk in llm_service.stream_chat_completion(message_history):
                full_response += chunk
                yield json.dumps({"data": chunk})
        
        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_msg)
        db.commit()
        
        yield json.dumps({"event": "end", "data": "done"})
        
    except Exception as e:
        logger.error(f"Error in chat streaming: {e}")
        yield json.dumps({"error": str(e)})


@router.post("/chat")
async def chat_stream(
    request: ChatRequest,
    db: SQLSession = Depends(get_session)
):
    async def event_generator():
        async for event in generate_sse_events(
            request.session_id,
            request.text,
            db
        ):
            yield f"data: {event}\n\n"
    
    return EventSourceResponse(event_generator())