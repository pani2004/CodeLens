# CodeLens AI 🔍

> AI-powered codebase analysis and understanding tool

CodeLens AI helps developers understand complex codebases through intelligent code analysis, semantic search, and interactive chat. Upload any GitHub repository and get instant insights through natural language conversations with your code.

![CodeLens AI](https://img.shields.io/badge/AI-Powered-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Next.js](https://img.shields.io/badge/Next.js-16+-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)

## ✨ Features

- **🤖 AI-Powered Code Analysis**: Chat with your codebase using Google Gemini AI
- **🔍 Semantic Search**: Vector-based code search powered by pgvector embeddings
- **📊 Interactive Graph Visualization**: Explore code relationships and dependencies with ReactFlow
- **📁 Smart File Explorer**: Browse repository structure with syntax highlighting
- **💬 Persistent Chat History**: Conversations saved per repository with session persistence
- **🔐 GitHub OAuth Integration**: Secure authentication and repository access
- **⚡ Real-time Streaming**: SSE-based streaming responses for instant feedback
- **📈 Usage Quota Tracking**: Monitor API usage and embedding generation

## 🏗️ Architecture

```
CodeLensAI/
├── backend/                 # FastAPI + Celery + PostgreSQL
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   ├── controllers/    # Business logic
│   │   ├── services/       # AI, GitHub, embeddings
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── tasks/          # Celery async tasks
│   │   └── middleware/     # Auth, CORS, rate limiting
│   ├── alembic/            # Database migrations
│   └── docker-compose.yml  # Infrastructure setup
│
└── client/                  # Next.js 16 + React 19
    ├── app/                # App router pages
    ├── components/         # React components
    │   ├── features/       # Feature-specific components
    │   └── ui/            # Reusable UI components
    └── lib/               # API clients, stores, utils
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL 16 + pgvector (vector embeddings)
- **Task Queue**: Celery + Redis
- **AI**: Google Gemini (gemini-2.5-flash, text-embedding-01)
- **Auth**: GitHub OAuth + JWT
- **ORM**: SQLAlchemy (async)

### Frontend
- **Framework**: Next.js 16 (React 19, App Router)
- **State Management**: Zustand + sessionStorage
- **Styling**: Tailwind CSS 4
- **UI Components**: Radix UI + shadcn/ui
- **Code Highlighting**: react-syntax-highlighter + Prism
- **Graph Visualization**: ReactFlow
- **Markdown**: react-markdown + remark-gfm

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** and **Docker Compose** (for backend services)
- **Node.js** 20+ and **npm** (for frontend)
- **Git** (for repository cloning)

You'll also need API keys for:
- **GitHub OAuth App** ([Create one](https://github.com/settings/developers))
- **Google Gemini API** ([Get key](https://aistudio.google.com/apikey))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CodeLensAI.git
cd CodeLensAI
```

### 2. Backend Setup

#### Create Environment File

```bash
cd backend
cp .env.example .env
```

#### Configure Environment Variables

Edit `.env` and fill in the required values:

```env
# GitHub OAuth (https://github.com/settings/developers)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback

# Gemini AI (https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_api_key

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your_secure_random_string

# Encryption Key (generate with command below)
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your_fernet_encryption_key
```

#### Start Backend Services

```bash
# Start PostgreSQL, Redis, FastAPI, and Celery
docker compose up -d

# Check logs
docker compose logs -f

# Verify services are running
docker compose ps
```

The backend will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd ../client
npm install
```

#### Create Environment File (Optional)

```bash
# Create .env.local if you need custom API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

#### Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📖 Usage

### 1. Sign In with GitHub

- Navigate to `http://localhost:3000`
- Click "Sign in with GitHub"
- Authorize the application

### 2. Analyze a Repository

- Click "Add Repository" or go to Repositories page
- Select or enter a GitHub repository URL
- Click "Analyze" to start processing
- Wait for analysis to complete (embedding generation)

### 3. Chat with Your Code

- Navigate to the repository's chat page
- Ask questions about the codebase:
  - "What does this application do?"
  - "Explain the authentication flow"
  - "Show me all the API endpoints"
  - "What database models are there?"

### 4. Explore the Graph

- Click "Graph View" to see code relationships
- Interactive nodes represent files and modules
- Zoom, pan, and click nodes for details

### 5. Browse Files

- Use the file explorer on the left
- Click any file to view with syntax highlighting
- Click "Explain" to ask AI about the file

## 🔧 Development

### Backend Development

```bash
cd backend

# Run migrations
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head

# View logs
docker compose logs -f backend
docker compose logs -f celery-worker

# Restart services after code changes
docker compose restart backend celery-worker

# Run tests (if available)
docker compose exec backend pytest
```

### Frontend Development

```bash
cd client

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Lint code
npm run lint
```

### Database Management

```bash
# Access PostgreSQL
docker compose exec db psql -U postgres -d codelens

# Backup database
docker compose exec db pg_dump -U postgres codelens > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U postgres codelens
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Auth** |
| GET | `/auth/github/login` | Get GitHub OAuth URL |
| POST | `/auth/github/callback` | Handle OAuth callback |
| GET | `/auth/me` | Get current user |
| POST | `/auth/refresh` | Refresh JWT token |
| POST | `/auth/logout` | Logout |
| **Repositories** |
| GET | `/repos` | List analyzed repositories |
| POST | `/repos/analyze` | Analyze new repository |
| GET | `/repos/{id}` | Get repository details |
| GET | `/repos/{id}/status` | Get analysis status |
| GET | `/repos/{id}/summary` | Get AI-generated summary |
| POST | `/repos/{id}/summary/regenerate` | Regenerate summary |
| DELETE | `/repos/{id}` | Delete repository |
| GET | `/repos/{id}/files` | Get file content |
| GET | `/repos/github/list` | List user's GitHub repos |
| GET | `/repos/quota` | Get usage quota |
| **Chat** |
| POST | `/chat` | Chat with AI (SSE streaming) |
| POST | `/chat/sync` | Chat with AI (non-streaming) |
| GET | `/chat/history/{repo_id}` | Get chat history |
| DELETE | `/chat/history/{repo_id}` | Clear chat history |
| GET | `/chat/prompts/{repo_id}` | Get suggested prompts |
| **Graph** |
| GET | `/repos/{id}/graph` | Get code dependency graph |

Full API documentation: `http://localhost:8000/docs`

## 🔐 Environment Variables

### Backend (.env)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | ✅ | - |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | ✅ | - |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ | - |
| `JWT_SECRET` | JWT signing secret | ✅ | - |
| `FERNET_KEY` | Encryption key for tokens | ✅ | - |
| `DATABASE_URL` | PostgreSQL connection (async) | ✅ | Set in docker-compose |
| `REDIS_URL` | Redis connection | ✅ | Set in docker-compose |
| `FRONTEND_URL` | Frontend URL for CORS | ✅ | `http://localhost:3000` |
| `GEMINI_MODEL` | Gemini model name | ❌ | `gemini-1.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model | ❌ | `text-embedding-004` |

### Frontend (.env.local)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ❌ | `http://localhost:8000` |


## 📊 Rate Limits

- **Gemini API (Free Tier)**: 100 requests/minute
- **Embedding Batches**: 25 chunks per batch, 18s delay
- **GitHub API**: 5,000 requests/hour (authenticated)


