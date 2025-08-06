from sqlmodel import Field, SQLModel
from datetime import datetime


class Summary(SQLModel, table=True):
    session_id: str = Field(foreign_key="session.id", primary_key=True)
    title: str = Field(max_length=80)
    markdown: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self):
        return f"<Summary(session_id={self.session_id}, title={self.title})>"