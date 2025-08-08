from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional
import uuid


class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(foreign_key="session.id", index=True)
    role: str = Field()  # Will be validated to be "user" or "assistant"
    content: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"