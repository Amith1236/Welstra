# Frontend-Backend Integration Guide

## Overview

The Welstra platform is now fully integrated with the React frontend and FastAPI backend working together seamlessly.

### Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│   React Frontend│                    │  FastAPI Backend│
│   (Vite + React)├───────API Calls───→│   (Python)      │
│                 │←─────JSON Data─────┤                 │
└─────────────────┘                    └─────────────────┘
       Port 5173                            Port 8000
 (dev) / Root (prod)           
```

## Development Setup

### Prerequisites
- Node.js 16+ and npm/yarn
- Python 3.10+ with pip
- Virtual environment (recommended)

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd Welstra
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Create .env file in Welstra directory with:
   OPENAI_API_KEY=your_key_here
   OPENAI_ENABLED=true  # or false for testing
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   ```

3. **Run backend:**
   ```bash
   # From Welstra directory
   python -m backend.main
   
   # Or using uvicorn directly:
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend runs at: http://localhost:8000

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd Welstra/frontend
   npm install
   ```

2. **Run development server (with API proxy):**
   ```bash
   npm run dev
   ```
   Frontend runs at: http://localhost:5173
   
   The proxy in `vite.config.js` automatically forwards API calls:
   - `/health` → http://localhost:8000/health
   - `/investigate` → http://localhost:8000/investigate
   - `/investigation/*` → http://localhost:8000/investigation/*
   - etc.

## Production Deployment

### Build Frontend

```bash
cd Welstra/frontend
npm run build
```

This creates a `dist/` directory with optimized static files.

### Prepare Backend

The backend is configured to serve the built frontend automatically:

1. Built frontend files go to: `frontend/dist/`
2. Backend detects and serves them when running on port 8000
3. All routes except API endpoints serve `index.html` (SPA routing)

### Run Production

```bash
# Single command starts everything
python -m backend.main
```

This will:
- Serve the React app at http://localhost:8000/
- Expose API endpoints at http://localhost:8000/api/*
- Handle SPA routing automatically

## API Endpoints

### Health & Config
- `GET /health` - Backend health check
- `GET /config` - Configuration and limits

### Investigation (Main Pipeline)
- `POST /investigate` - Create and start investigation
- `GET /investigation/{investigation_id}` - Get investigation status
- `GET /investigations` - List all investigations
- `DELETE /investigation/{investigation_id}` - Cancel investigation

### Response Format

All responses follow this pattern (defined in `models/schemas.py`):

```python
InvestigationResponse(
    investigation_id: str
    status: "running" | "completed" | "failed" | "queued"
    report: InvestigationReport | None
    activity_log: list[ActivityLogEntry]
    error: str | None
)
```

## Frontend API Integration

The frontend uses the `getApiUrl()` helper function to build API URLs:

```javascript
// Development: Proxies through Vite
getApiUrl("/investigate") → http://localhost:8000/investigate (via proxy)

// Production: Relative URLs
getApiUrl("/investigate") → /investigate (served by same backend)
```

All fetch calls automatically use the correct URL based on environment:

```javascript
// Example: Start investigation
const response = await fetch(getApiUrl("/investigate"), {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ resume_text: "..." })
});
```

## File Structure

```
Welstra/
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── __main__.py          # Entry point
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Styles (Tailwind)
│   ├── index.html           # HTML template
│   ├── vite.config.js       # Vite config with proxy
│   ├── package.json         # Frontend dependencies
│   └── dist/                # Built files (after npm run build)
├── agents/                  # 7-agent pipeline
├── models/                  # Pydantic schemas
├── services/                # Orchestrator & utilities
└── INTEGRATION_GUIDE.md     # This file
```

## Troubleshooting

### Frontend can't connect to backend

**Development:**
- Ensure backend is running: `python -m backend.main`
- Check backend is on port 8000
- Proxy is defined in `vite.config.js`

**Production:**
- Ensure frontend is built: `npm run build` in `/frontend`
- Check `frontend/dist/` exists
- Backend detects and serves it automatically

### CORS errors
- CORS is enabled in backend for all origins (development/testing)
- For production, update config in `backend/main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://yourdomain.com"],  # Specify your domain
      ...
  )
  ```

### Import errors
- Ensure Python virtual environment is activated
- All dependencies listed in `requirements.txt` are installed
- Check `pyproject.toml` for the correct Python version

## Development Workflow

### Adding a new API endpoint:

1. **Add schema in `models/schemas.py`:**
   ```python
   class MyRequest(BaseModel):
       field: str
   ```

2. **Add endpoint in `backend/main.py`:**
   ```python
   @app.post("/my-endpoint")
   async def my_endpoint(payload: MyRequest):
       return {"result": "data"}
   ```

3. **Call from frontend in `src/App.jsx`:**
   ```javascript
   const res = await fetch(getApiUrl("/my-endpoint"), {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ field: "value" })
   });
   ```

### Adding new React components:

Create components in `frontend/src/` and import in `App.jsx`:

```javascript
// frontend/src/components/MyComponent.jsx
export function MyComponent() {
  return <div>Hello</div>;
}

// frontend/src/App.jsx
import { MyComponent } from "./components/MyComponent";
```

## Environment Variables

### Backend (`Welstra/.env`)
```
OPENAI_API_KEY=sk-xxx                  # Your OpenAI API key
OPENAI_ENABLED=true                   # Enable/disable OpenAI features
BACKEND_HOST=0.0.0.0                  # Listen on all interfaces
BACKEND_PORT=8000                     # Backend port
```

### Frontend
- No `.env` file needed
- Uses relative URLs in production
- Uses proxy in development (configured in `vite.config.js`)

## Performance Optimization

### Frontend
- Built with Vite for fast development
- Tailwind CSS for optimized styling
- Minified on production build

### Backend
- Async/await for all I/O operations
- In-memory caching for investigations
- Streaming responses (if needed)

## Next Steps

1. **Install dependencies:**
   - Backend: `pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`

2. **Configure `.env` file** with your API keys

3. **Run in development:**
   ```bash
   # Terminal 1 - Backend
   python -m backend.main
   
   # Terminal 2 - Frontend  
   cd frontend && npm run dev
   ```

4. **Access at:** http://localhost:5173

5. **Build for production:**
   ```bash
   cd frontend && npm run build
   python -m backend.main  # Serves built frontend
   ```

## Support

For issues or questions:
1. Check console errors (both browser DevTools and terminal)
2. Review API response status codes
3. Check `logs/job_matcher.log` for backend errors
4. Verify all environment variables are set
