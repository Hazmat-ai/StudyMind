# StudyMind — AI-Powered Study Assistant

A full-stack web app that turns your lecture notes, textbook excerpts, and PDFs into flashcards, summaries, practice questions, and key concept breakdowns — instantly. Built with FastAPI, React, and the Claude API.

![StudyMind Demo](docs/demo.gif)

---

## Why I Built This

As a TA for Calculus and Information Technology at Wilfrid Laurier University, I watch students struggle every week with the same problem: they have the notes, but they don't know how to study from them. Highlighting and re-reading doesn't work. Active recall does — but making flashcards and practice questions by hand takes forever.

StudyMind automates the part that students skip. Paste your notes in, get a full study set out. It's the tool I wish existed when I was studying for midterms.

---

## Features

- **AI-generated flashcards** — term/definition pairs extracted from your content
- **Concise summary** — the key ideas in plain language, not a wall of bullet points
- **Practice questions** — short-answer and multiple choice with revealed answers
- **Key concept map** — a list of the most important terms and how they connect
- **Save study sets** — create an account, save your sets, come back later
- **PDF upload** — paste text or upload a PDF directly
- **Clean, focused UI** — designed to get out of your way while you study

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS, React Router |
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| AI | Anthropic Claude API (claude-sonnet) |
| Auth | JWT (python-jose + passlib) |
| PDF parsing | PyMuPDF (fitz) |
| Deployment | Vercel (frontend), Railway (backend + DB) |

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL (local or Railway)
- Anthropic API key

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/studymind.git
cd studymind
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `/backend`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/studymind
ANTHROPIC_API_KEY=your_key_here
SECRET_KEY=your_jwt_secret_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Run migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd frontend
npm install
```

Create a `.env.local` file in `/frontend`:

```env
VITE_API_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

App runs at `http://localhost:5173`.

---

## Project Structure

```
studymind/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routers/
│   │   │   ├── auth.py          # Register, login, JWT
│   │   │   ├── generate.py      # AI generation endpoint
│   │   │   └── studysets.py     # Save/load/delete study sets
│   │   ├── models/
│   │   │   ├── user.py          # User model
│   │   │   └── studyset.py      # StudySet + Card models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ai.py            # Claude API calls + prompt logic
│   │   │   └── pdf.py           # PDF text extraction
│   │   └── database.py          # SQLAlchemy session setup
│   ├── alembic/                 # DB migrations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx         # Landing + input page
│   │   │   ├── Results.jsx      # Generated study set view
│   │   │   ├── Dashboard.jsx    # Saved sets list
│   │   │   └── Auth.jsx         # Login / register
│   │   ├── components/
│   │   │   ├── FlashCard.jsx    # Flip card interaction
│   │   │   ├── PracticeQ.jsx    # Question reveal component
│   │   │   ├── SummaryPanel.jsx
│   │   │   └── ConceptList.jsx
│   │   ├── hooks/
│   │   │   ├── useAuth.js       # Auth context + token handling
│   │   │   └── useStudySet.js   # Generate + save logic
│   │   └── api/
│   │       └── client.js        # Axios instance + interceptors
│   └── package.json
│
└── README.md
```

---

## Key Technical Decisions

**Why FastAPI over Flask?**
FastAPI gives automatic OpenAPI docs, native async support, and Pydantic validation out of the box. For an AI app where the bottleneck is the LLM API call (not the DB), async matters — the server can handle other requests while waiting on Claude rather than blocking the thread.

**Why structured prompting over a chat interface?**
I prompt Claude to return strict JSON with defined keys (`summary`, `flashcards`, `questions`, `concepts`). This makes the frontend rendering deterministic and removes the need to parse freeform markdown. The tradeoff is less flexibility in the AI output, which is the right call for a tool app where consistency matters more than creativity.

**Why PyMuPDF for PDFs?**
Faster and more reliable text extraction than pdfplumber for typical student PDFs (lecture slides exported as PDF, textbook chapters). Falls back gracefully on scanned documents by returning a helpful error rather than garbage output.

**Why JWT over sessions?**
The frontend and backend are on separate domains (Vercel + Railway), so cookie-based sessions require more CORS configuration and SameSite handling. JWTs are stateless and work cleanly across origins. Tokens expire in 60 minutes with refresh on activity.

---

## API Reference

### `POST /generate`
Generates a study set from text input.

**Request body:**
```json
{
  "content": "string (raw text or extracted PDF text)",
  "options": {
    "num_flashcards": 10,
    "num_questions": 5,
    "difficulty": "university"
  }
}
```

**Response:**
```json
{
  "summary": "string",
  "flashcards": [{ "term": "string", "definition": "string" }],
  "questions": [{ "question": "string", "answer": "string", "type": "short_answer" }],
  "concepts": [{ "term": "string", "related": ["string"] }]
}
```

### `POST /auth/register` / `POST /auth/login`
Standard JWT auth flow. Login returns `access_token`.

### `GET /studysets` / `POST /studysets` / `DELETE /studysets/{id}`
CRUD for saved study sets. All routes require `Authorization: Bearer <token>`.

---

## Deployment

**Frontend (Vercel):**
Connect the `/frontend` directory. Set `VITE_API_URL` to your Railway backend URL.

**Backend (Railway):**
Connect the `/backend` directory. Railway auto-detects Python. Add environment variables in the Railway dashboard. Provision a Postgres plugin and Railway injects `DATABASE_URL` automatically.

Run migrations on first deploy:
```bash
railway run alembic upgrade head
```

---

## Roadmap

- [ ] Spaced repetition scheduling (SM-2 algorithm)
- [ ] Export to Anki-compatible `.apkg` format
- [ ] Chrome extension to generate from any webpage
- [ ] Collaborative study sets (share with classmates)
- [ ] Better handling of math notation in STEM content

---

## License

MIT
