# Welstra — AI Interview Planner (Frontend)

React + Tailwind SPA. Clean OpenAI-style UI.

## Quick Start

```bash
npm install
npm run dev
```

App runs on `http://localhost:5173`, proxies `/api/*` → `http://localhost:8000`.

---

## Dev Mode

There's a **"Use mock data"** checkbox bottom-right of the form. Tick it to test the full UI without a backend.

---

## API Contract

The frontend expects a FastAPI backend at `localhost:8000`.

### POST `/api/analyze`

**Request:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `resume` | File (.pdf / .docx) | ✅ |
| `job_title` | string | ✅ |
| `company` | string | ✅ |
| `telegram_handle` | string | ❌ |

**Response JSON:**

```json
{
  "job_title": "Software Engineer",
  "company": "Stripe",
  "company_overview": {
    "summary": "...",
    "highlights": [
      { "label": "Founded", "value": "2010" }
    ]
  },
  "department_info": "...",
  "role_breakdown": {
    "responsibilities": ["..."]
  },
  "requirements": ["..."],
  "interview_questions": [
    { "question": "...", "source": "Glassdoor, 2024" }
  ],
  "resume_tips": {
    "strengths": ["..."],
    "gaps": ["..."],
    "action_items": ["..."]
  },
  "application_link": "https://...",
  "glassdoor_link": "https://...",
  "already_subscribed_telegram": false
}
```

### POST `/api/subscribe-telegram`

**Request JSON:**
```json
{
  "telegram_handle": "username",
  "job_title": "Software Engineer",
  "company": "Stripe"
}
```

**Response:** `{ "ok": true }`

---

## File Structure

```
src/
├── api/
│   └── client.js          # axios API calls — edit base URL here
├── components/
│   ├── Header.jsx
│   ├── InputForm.jsx       # resume upload + job/company input
│   ├── ResultPanel.jsx     # company overview, role, questions, tips
│   └── LoadingState.jsx    # animated loading steps
├── App.jsx                 # layout + state management + mock toggle
└── index.css               # tailwind + component classes
```
