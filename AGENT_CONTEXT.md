# StudyMind — Agent Context

This file gives an AI coding assistant full context on the StudyMind project so it can contribute meaningfully without needing long explanations each session. Read this before writing any code.

---

## What this app is

StudyMind is an AI-powered study assistant. Students paste in lecture notes or upload a PDF and get back a structured study set: a summary, flashcards, practice questions, and a key concepts list. Users can create accounts and save their study sets.

The core value is speed and quality of active recall material. The app should feel like a smart study partner, not a generic AI tool.

---

## Who built it and why

Built by Hamza, a 2nd-year Computer Science + UX Design student at Wilfrid Laurier University. Also a TA for Calculus and IT — so the target user is literally the person building it. Design decisions should reflect real student workflows, not hypothetical ones.

---

## Tech stack (non-negotiable)

| Layer | Tech | Notes |
|---|---|---|
| Backend | Python 3.11, FastAPI | Async, Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic | Use mapped_column syntax |
| AI | Anthropic Claude API | claude-sonnet-4-20250514, structured JSON output |
| Auth | JWT via python-jose, passlib[bcrypt] | 60 min expiry, refresh on activity |
| PDF | PyMuPDF (fitz) | Prefer over pdfplumber |
| Frontend | React 18, Vite, Tailwind CSS, React Router v6 | No Next.js |
| HTTP client | Axios | With interceptors for auth headers |
| Deployment | Railway (backend), Vercel (frontend) | |

Do not suggest switching any of these unless there is a critical technical reason. Don't suggest Next.js — the project is intentionally a SPA with a separate API.

---

## Directory layout

```
studymind/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── generate.py
│   │   │   └── studysets.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   └── studyset.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── generate.py
│   │   │   └── studyset.py
│   │   ├── services/
│   │   │   ├── ai.py
│   │   │   └── pdf.py
│   │   └── database.py
│   ├── alembic/
│   ├── .env
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Results.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Auth.jsx
│   │   ├── components/
│   │   │   ├── FlashCard.jsx
│   │   │   ├── PracticeQ.jsx
│   │   │   ├── SummaryPanel.jsx
│   │   │   └── ConceptList.jsx
│   │   ├── hooks/
│   │   │   ├── useAuth.js
│   │   │   └── useStudySet.js
│   │   └── api/
│   │       └── client.js
│   ├── .env.local
│   └── package.json
```

---

## Data models

### User
```python
id: UUID (primary key)
email: str (unique, indexed)
hashed_password: str
created_at: datetime
study_sets: relationship -> StudySet
```

### StudySet
```python
id: UUID (primary key)
user_id: UUID (FK -> users.id)
title: str  # auto-generated from content, user can rename
source_text: str  # original input, stored for regeneration
summary: str
created_at: datetime
updated_at: datetime
flashcards: relationship -> Flashcard
questions: relationship -> Question
concepts: JSON field  # list of {term, related[]}
```

### Flashcard
```python
id: UUID
study_set_id: UUID (FK)
term: str
definition: str
order_index: int
```

### Question
```python
id: UUID
study_set_id: UUID (FK)
question: str
answer: str
question_type: enum ('short_answer', 'multiple_choice')
options: JSON  # only populated for multiple_choice
order_index: int
```

---

## AI service — how it works

The AI logic lives entirely in `backend/app/services/ai.py`. The key design decision is **structured JSON output** — Claude is prompted to return a strict JSON object, never markdown prose. This makes frontend rendering deterministic.

### Prompt architecture

```python
SYSTEM_PROMPT = """
You are a study assistant that converts academic content into structured study materials.
Always respond with valid JSON only. No preamble, no markdown, no explanation outside the JSON.

Output format:
{
  "title": "short descriptive title (max 8 words)",
  "summary": "2-4 paragraph summary of the core ideas in plain language",
  "flashcards": [
    { "term": "...", "definition": "..." }
  ],
  "questions": [
    {
      "question": "...",
      "answer": "...",
      "type": "short_answer"
    }
  ],
  "concepts": [
    { "term": "...", "related": ["...", "..."] }
  ]
}

Guidelines:
- Flashcards should test understanding, not just memorization
- Questions should require actual comprehension to answer, not just recall
- Summaries should explain WHY things work, not just WHAT they are
- Use plain language — imagine explaining to a smart peer, not a professor
- Generate exactly the number of flashcards and questions requested
"""

USER_PROMPT_TEMPLATE = """
Generate a study set from the following academic content.
Number of flashcards: {num_flashcards}
Number of questions: {num_questions}
Difficulty level: {difficulty}

Content:
{content}
"""
```

### Calling the API

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

async def generate_study_set(content: str, options: GenerateOptions) -> StudySetData:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                num_flashcards=options.num_flashcards,
                num_questions=options.num_questions,
                difficulty=options.difficulty,
                content=content[:12000]  # truncate to avoid token overflow
            )
        }]
    )
    
    raw = message.content[0].text
    data = json.loads(raw)  # Claude returns clean JSON per system prompt
    return StudySetData(**data)
```

Always truncate input content to ~12,000 characters to stay within token limits. If the user uploads a long PDF, extract the most content-dense pages first.

---

## Frontend — design principles

The UI is intentionally minimal and focused. Students use this when they're stressed and time-poor. Every extra click is friction.

**Core design rules:**
- Dark mode default. Students study at night.
- No sidebars, no dashboards cluttering the main flow. The generation input is the hero element.
- FlashCard component uses CSS flip animation on click — no libraries needed.
- PracticeQ component shows question, hides answer behind a "Reveal" button. No fancy animation, just a clean toggle.
- Results page uses tabs: Summary / Flashcards / Practice / Concepts. Tab state is URL-synced (`?tab=flashcards`) so users can share or bookmark a specific view.
- Loading state during generation should show a skeleton, not a spinner. The wait is 3-8 seconds — a spinner feels like it's stuck, a skeleton feels like it's loading.

**Color palette (Tailwind):**
- Background: `slate-900` / `slate-800`
- Cards: `slate-700`
- Accent: `violet-500` (primary actions, highlights)
- Text: `slate-100` (primary), `slate-400` (secondary)
- Success: `emerald-400`
- Borders: `slate-600`

**Do not:**
- Use any component library (shadcn, MUI, Chakra). Everything is custom Tailwind.
- Add animations beyond the flashcard flip and subtle fade-ins on load.
- Show the raw JSON or API response to the user at any point.

---

## Auth flow

1. User registers with email + password. Password is bcrypt hashed, never stored plain.
2. Login returns a JWT access token (60 min expiry).
3. Frontend stores token in `localStorage` (acceptable for this scope — not a banking app).
4. Axios interceptor attaches `Authorization: Bearer <token>` to every request.
5. FastAPI dependency `get_current_user` decodes the token and returns the user or raises 401.
6. On 401, the frontend clears the token and redirects to `/auth`.

---

## Error handling conventions

**Backend:**
- Use FastAPI's `HTTPException` for all client errors. Never let unhandled exceptions reach the client.
- Wrap Claude API calls in try/except. If the API fails, return a 503 with a user-friendly message.
- If JSON parsing of Claude's response fails, retry once with a stricter prompt before returning 500.
- Log all errors with enough context to debug (user_id, content_length, model, error).

**Frontend:**
- All API calls go through the central `api/client.js` Axios instance.
- Display user-friendly error messages, never raw API error strings.
- Generation errors should offer a retry button, not just a message.
- Auth errors (401) should silently redirect to login, not show an error page.

---

## Environment variables

**Backend `.env`:**
```
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=<random 32-byte hex>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=http://localhost:5173,https://studymind.vercel.app
```

**Frontend `.env.local`:**
```
VITE_API_URL=http://localhost:8000
```

---

## What's intentionally not built yet

These are known gaps, not oversights. Don't implement them unless asked:

- Spaced repetition / scheduling
- Anki export
- Social / sharing features
- Mobile app
- Markdown rendering in summaries (plain text is fine for now)
- Rate limiting on the generate endpoint (add before going public)

---

## Code style preferences

- Python: type hints everywhere, Pydantic v2 models for all schemas, async functions for route handlers
- JavaScript: functional components only, hooks for all stateful logic, no class components
- No inline styles in JSX — Tailwind classes only
- Commit messages: conventional commits format (`feat:`, `fix:`, `refactor:`)
- No `console.log` left in production code

---

## How to continue a session

When starting a new session with this context file, the AI assistant should:

1. Read this file fully before writing any code
2. Ask which part of the app is being worked on if it's not clear
3. Follow the tech stack, data models, and conventions defined here exactly
4. Check the existing directory structure before creating new files
5. Write code that looks like a real developer wrote it — consistent style, real variable names, actual error handling, not tutorial-quality placeholders

The goal is a polished, deployable app that Hamza can demo and discuss in a co-op interview. Every piece of code should reflect that standard.
