from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional
import uuid


class Session(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: Optional[str] = Field(default=None, max_length=80)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self):
        return f"<Session(id={self.id}, title={self.title})>"