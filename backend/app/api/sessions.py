from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as SQLSession, select
from typing import List, Dict, Any
from datetime import datetime
import uuid

from ..database import get_session
from ..models import Session, Message, Summary
from ..services import SummarizerService, NotionWriter
from ..config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/sessions")


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class SummaryRequest(BaseModel):
    pass


class SummaryResponse(BaseModel):
    title: str
    markdown: str


class NotionResponse(BaseModel):
    page_id: str
    url: str


@router.post("")
async def create_session(db: SQLSession = Depends(get_session)):
    session = Session()
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {"id": session.id}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: SQLSession = Depends(get_session)
):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    statement = select(Message).where(
        Message.session_id == session_id
    ).order_by(Message.created_at)
    
    messages = db.exec(statement).all()
    
    return {
        "messages": [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            ) for msg in messages
        ]
    }


@router.post("/{session_id}/summarize")
async def summarize_session(
    session_id: str,
    db: SQLSession = Depends(get_session)
):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    existing_summary = db.get(Summary, session_id)
    if existing_summary:
        return SummaryResponse(
            title=existing_summary.title,
            markdown=existing_summary.markdown
        )
    
    statement = select(Message).where(
        Message.session_id == session_id
    ).order_by(Message.created_at)
    
    messages = db.exec(statement).all()
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")
    
    message_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    async with SummarizerService() as summarizer:
        title, markdown = await summarizer.summarize_session(message_dicts)
    
    summary = Summary(
        session_id=session_id,
        title=title,
        markdown=markdown
    )
    db.add(summary)
    
    if not session.title:
        session.title = title
    
    db.commit()
    
    return SummaryResponse(title=title, markdown=markdown)


@router.post("/{session_id}/notion")
async def save_to_notion(
    session_id: str,
    db: SQLSession = Depends(get_session)
):
    if not settings.notion_api_key or not settings.notion_parent_page_id:
        raise HTTPException(
            status_code=400,
            detail="Notion API key or parent page ID not configured"
        )
    
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    summary = db.get(Summary, session_id)
    
    if not summary:
        statement = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at)
        
        messages = db.exec(statement).all()
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages to save")
        
        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with SummarizerService() as summarizer:
            title, markdown = await summarizer.summarize_session(message_dicts)
        
        summary = Summary(
            session_id=session_id,
            title=title,
            markdown=markdown
        )
        db.add(summary)
        
        if not session.title:
            session.title = title
        
        db.commit()
    
    notion_writer = NotionWriter(
        settings.notion_api_key,
        settings.notion_parent_page_id
    )
    
    try:
        result = await notion_writer.create_notion_page(
            summary.title,
            summary.markdown
        )
        
        return NotionResponse(
            page_id=result["page_id"],
            url=result["url"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to create Notion page: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: SQLSession = Depends(get_session)
):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at
    )