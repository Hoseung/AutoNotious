import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session as SQLSession, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock
import json

from app.main import app
from app.database import get_session
from app.models import Session, Message, Summary


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with SQLSession(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: SQLSession):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient):
        response = client.get("/api/healthz")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestSessionEndpoints:
    def test_create_session(self, client: TestClient):
        response = client.post("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 36
    
    def test_get_session(self, client: TestClient, session: SQLSession):
        test_session = Session(title="Test Session")
        session.add(test_session)
        session.commit()
        
        response = client.get(f"/api/sessions/{test_session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_session.id
        assert data["title"] == "Test Session"
    
    def test_get_session_not_found(self, client: TestClient):
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_messages(self, client: TestClient, session: SQLSession):
        test_session = Session()
        session.add(test_session)
        
        msg1 = Message(
            session_id=test_session.id,
            role="user",
            content="Hello"
        )
        msg2 = Message(
            session_id=test_session.id,
            role="assistant",
            content="Hi there!"
        )
        session.add(msg1)
        session.add(msg2)
        session.commit()
        
        response = client.get(f"/api/sessions/{test_session.id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["content"] == "Hi there!"
    
    @pytest.mark.asyncio
    async def test_summarize_session(self, client: TestClient, session: SQLSession):
        test_session = Session()
        session.add(test_session)
        
        msg1 = Message(
            session_id=test_session.id,
            role="user",
            content="Tell me about Python"
        )
        msg2 = Message(
            session_id=test_session.id,
            role="assistant",
            content="Python is a programming language"
        )
        session.add(msg1)
        session.add(msg2)
        session.commit()
        
        with patch('app.services.summarizer.SummarizerService.summarize_session') as mock_summarize:
            mock_summarize.return_value = (
                "Python Discussion",
                "# Python Discussion\n\n## TL;DR\n- Discussed Python\n\n## Key Points\n- Python is a language"
            )
            
            response = client.post(f"/api/sessions/{test_session.id}/summarize")
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Python Discussion"
            assert "# Python Discussion" in data["markdown"]
    
    @pytest.mark.asyncio
    async def test_save_to_notion(self, client: TestClient, session: SQLSession):
        test_session = Session()
        session.add(test_session)
        
        summary = Summary(
            session_id=test_session.id,
            title="Test Summary",
            markdown="# Test\n\nContent"
        )
        session.add(summary)
        session.commit()
        
        with patch('app.config.settings.notion_api_key', 'test_key'):
            with patch('app.config.settings.notion_parent_page_id', 'test_parent'):
                with patch('app.services.notion_writer.NotionWriter.create_notion_page') as mock_create:
                    mock_create.return_value = {
                        "page_id": "test_page_id",
                        "url": "https://notion.so/test"
                    }
                    
                    response = client.post(f"/api/sessions/{test_session.id}/notion")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["page_id"] == "test_page_id"
                    assert data["url"] == "https://notion.so/test"


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_stream(self, client: TestClient, session: SQLSession):
        test_session = Session()
        session.add(test_session)
        session.commit()
        
        with patch('app.services.llm_service.LLMService.stream_chat_completion') as mock_stream:
            async def mock_generator():
                yield "Hello"
                yield " world"
            
            mock_stream.return_value = mock_generator()
            
            response = client.post(
                "/api/chat",
                json={"session_id": test_session.id, "text": "Hi"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"