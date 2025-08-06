# Local Chat App with Notion Integration

A ChatGPT-style local web application with session management, streaming responses, and Notion export capabilities.

## Features

- 💬 ChatGPT-like conversational interface
- 🔄 Real-time streaming responses via SSE
- 📝 Automatic session summarization
- 📚 Export conversations to Notion
- 💾 Persistent chat history
- 🧪 Fully testable modular components

## Architecture

### Backend (FastAPI + Python)
- **Models**: Session, Message, Summary (SQLModel/SQLite)
- **Services**: 
  - LLMService: LiteLLM integration for OpenAI API
  - SummarizerService: Chunked map-reduce summarization
  - NotionWriter: Markdown to Notion blocks conversion
- **API**: RESTful endpoints + SSE for streaming

### Frontend (React + TypeScript)
- Real-time chat UI with streaming support
- Session management
- Notion export with one click

## Setup

### Prerequisites
- Python 3.13 (via uv)
- Node.js 18+
- OpenAI API key
- Notion API key (optional, for export feature)

### Backend Setup

1. Activate Python virtual environment:
```bash
source .venv/bin/activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start LiteLLM proxy (in a separate terminal):
```bash
litellm --model gpt-4o-mini --port 4000
```

5. Run the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:5173 in your browser

## Configuration

### Environment Variables (.env)

- `OPENAI_API_KEY`: Your OpenAI API key
- `MODEL`: LLM model to use (default: gpt-4o-mini)
- `NOTION_API_KEY`: Notion integration token
- `NOTION_PARENT_PAGE_ID`: Parent page ID for saving conversations
- `MAX_CONTEXT_TOKENS`: Maximum tokens for chat context (default: 5000)

### Getting Notion Credentials

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Copy the Internal Integration Token as `NOTION_API_KEY`
3. Share a Notion page with your integration
4. Copy the page ID from the URL as `NOTION_PARENT_PAGE_ID`

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

Test coverage includes:
- Unit tests for LLMService, SummarizerService, NotionWriter
- Integration tests for API endpoints
- Mocked external dependencies for isolated testing

### Frontend Tests

```bash
cd frontend
npm test
```

## API Documentation

### Endpoints

- `GET /api/healthz` - Health check
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/messages` - Get session messages
- `POST /api/chat` - Stream chat response (SSE)
- `POST /api/sessions/{id}/summarize` - Generate session summary
- `POST /api/sessions/{id}/notion` - Export to Notion

## Development

### Project Structure

```
AutoNotoin/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   └── tests/            # Test files
├── frontend/
│   └── src/
│       ├── components/   # React components
│       └── services/     # API clients
└── .env                  # Configuration
```

### Debugging Tips

1. **Backend logs**: Check uvicorn output for API errors
2. **LiteLLM logs**: Monitor proxy terminal for LLM issues
3. **Frontend console**: Browser DevTools for client-side errors
4. **Database**: SQLite file at `./app.db` for persistence issues

## License

MIT