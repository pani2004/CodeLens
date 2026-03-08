# CodeLens AI — Backend

AI-powered codebase analysis tool backend built with **FastAPI**, **PostgreSQL + pgvector**, **LangChain + Gemini**, and **Celery**.

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app init
│   ├── config.py            # Pydantic BaseSettings
│   ├── database.py          # Async SQLAlchemy + pgvector
│   ├── routes/              # API endpoints
│   ├── controllers/         # Business logic
│   ├── services/            # Core services (GitHub, AI, parsing, graphs)
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── middleware/          # Auth, rate limiting, CORS
│   ├── utils/               # Crypto, JWT, validators, audit
│   └── tasks/               # Celery async tasks
├── alembic/                 # Database migrations
├── docker-compose.yml       # PostgreSQL + Redis + Backend + Celery
└── requirements.txt
```



## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/github/login` | Get GitHub OAuth URL |
| POST | `/auth/github/callback` | Handle OAuth callback |
| GET | `/auth/me` | Get current user |
| POST | `/auth/refresh` | Refresh JWT token |
| POST | `/auth/logout` | Logout |
| GET | `/repos` | List repositories |
| POST | `/repos/analyze` | Analyze new repo |
| GET | `/repos/{id}` | Get repository |
| GET | `/repos/{id}/status` | Get analysis status |
| GET | `/repos/{id}/summary` | Get repo summary |
| POST | `/repos/{id}/summary/regenerate` | Regenerate summary |
| DELETE | `/repos/{id}` | Delete repository |
| GET | `/repos/github/list` | List GitHub repos |
| GET | `/repos/quota` | Get usage quota |
| POST | `/chat` | Chat (SSE streaming) |
| POST | `/chat/sync` | Chat (non-streaming) |
| GET | `/chat/history/{repo_id}` | Get chat history |
| DELETE | `/chat/history/{repo_id}` | Clear history |
| GET | `/chat/prompts/{repo_id}` | Get suggested prompts |
| GET | `/analysis/{repo_id}/graph` | Dependency graph |
| GET | `/analysis/{repo_id}/flows` | Execution flows |
| GET | `/analysis/{repo_id}/flows/{id}` | Flow detail |
| GET | `/health` | Health check |

## Tech Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy 2.0** — async ORM with pgvector support
- **PostgreSQL + pgvector** — vector database for embeddings
- **Redis** — caching, Celery broker, rate limiting
- **Celery** — distributed task queue
- **LangChain + Gemini** — RAG pipeline for code Q&A
- **networkx** — dependency graph analysis
- **tree-sitter** — code parsing





