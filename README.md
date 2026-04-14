# Troopod Ad-to-LP Harmonizer

AI-powered landing page personalization that harmonizes your ad creative with your landing page using CRO principles.

## 🎯 What This Does

Upload an ad creative image + enter a landing page URL → Get a personalized landing page where the copy is aligned to your ad, improving message consistency and conversion rates.

**Key Insight**: The personalized page is NOT a completely new page — it's the existing page enhanced with CRO-optimized copy matched to the ad creative.

---

## 🏗️ System Architecture

```
User → Next.js Frontend → FastAPI Orchestrator → {DOM Scraper, Vision Agent, Copywriter Agent} → Personalized Page
```

### 4-Step Pipeline

| Step | Component | What It Does |
|------|-----------|-------------|
| 1. Data Extraction | DOM Scraper (BeautifulSoup) | Fetches landing page HTML, extracts key text nodes (H1, H2, CTAs, paragraphs) with CSS selectors |
| 2. Context Generation | Vision Agent (Gemini Flash Latest) | Analyzes the ad image to extract: hook, offer, audience, tone, keywords, CTA |
| 3. CRO Copywriting | Copywriter Agent (Gemini Flash Latest) | Generates replacement text using ad context + original nodes, applying CRO principles |
| 4. Render & Return | Merger Module | Surgically replaces text in original HTML by CSS selector, preserving all layout/CSS/JS |

---

## 🧩 Key Components

### Backend (`/backend`)

| File | Role |
|------|------|
| `app/main.py` | FastAPI entry point — initializes app and includes routes |
| `app/api/routes.py` | API routes and endpoint handlers |
| `app/services/cache.py` | In-memory cache for personalizations |
| `app/scrape/scraper.py` | DOM scraper using Playwright — extracts text nodes with visual hierarchy data |
| `app/agents/vision_agent.py` | Gemini Vision API integration — analyzes ad creatives |
| `app/agents/copywriter_agent.py` | Gemini text model — generates CRO-optimized replacement copy |
| `app/agents/merger_agent.py` | HTML merger — applies text replacements preserving layout |
| `app/orchestration/graph.py` | LangGraph Orchestrator — coordinates the pipeline |

### Frontend (`/frontend`)

| File | Role |
|------|------|
| `src/app/page.tsx` | Main UI — upload zone, URL input, results display |
| `src/app/globals.css` | Premium dark theme with glassmorphism design |
| `src/app/layout.tsx` | Root layout with SEO meta tags |

---

## 🛡️ Guardrails: Preventing Bad Outputs

### Random/Unexpected Changes
- **Text-only modifications**: Copywriter outputs ONLY replacement text, never HTML/CSS/JS
- **Length enforcement**: Replacements must stay within ±30% of original text length (rejected otherwise)
- **Selector-based targeting**: Changes are mapped to specific CSS selectors, preventing unintended modifications
- **Node limit**: Max 20 nodes extracted, top 8 replacements generated (quality over quantity)

### Broken UI Prevention
- **Layout preservation**: Never modify CSS, images, scripts, or DOM structure — only text content
- **HTML validation**: After merging, the modified HTML is re-parsed to verify structural integrity
- **Rollback**: If any merge validation fails, the original HTML is returned with error indicators
- **Sandboxed iframes**: Preview renders in sandbox to prevent script execution

### Hallucination Prevention
- **Strict JSON schema**: Both Vision and Copywriter agents output Pydantic-validated JSON
- **Low temperature**: Vision (0.2) and Copywriter (0.3) — reduces creative variance
- **Context grounding**: Copywriter receives EXACT original text nodes as input, so replacements are grounded
- **No fabrication rule**: System prompt states "Do NOT invent features, prices, or claims not present in the ad"
- **HTML tag rejection**: Post-validation strips any replacement containing HTML tags

### Inconsistent Outputs
- **Deterministic system prompts**: Fixed prompts with explicit output schemas
- **Retry logic**: Up to 3 automated retries if JSON validation fails
- **Caching**: Same ad+URL combination returns cached result for 1 hour
- **Post-validation**: Length ratio checks, HTML tag detection, schema enforcement

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Installs FastAPI, Uvicorn, Playwright, etc.
playwright install               # Downloads the required browser binaries for Playwright

# Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start server
python3 -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Open the App
Visit `http://localhost:3000` in your browser.

---

## 🚀 Deployment

The project is structured to be seamlessly deployed with modern web services:
- **Frontend**: Deploy easily using **Vercel**. Connect your repository and configure the `NEXT_PUBLIC_API_URL` environment variable to point to your backend.
- **Backend**: Deploy on **Render** using a Web Service. Set the Build Command to `./build.sh` (which installs both python requirements and playwright binaries) and Start Command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

---

## 📁 Project Structure

```
Troopod/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   └── routes.py        # API routes
│   │   ├── core/
│   │   │   ├── config.py        # Configuration
│   │   │   └── state.py         # LangGraph state schema
│   │   ├── orchestration/
│   │   │   └── graph.py         # LangGraph workflow
│   │   ├── agents/              # Agent definitions
│   │   ├── services/            # Business logic services
│   │   └── scrape/              # Scraping utilities
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Env template
│   └── .env                  # Your API keys (gitignored)
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx          # Main UI
│   │   ├── globals.css       # Dark theme styles
│   │   └── layout.tsx        # Root layout
│   ├── .env.local            # Frontend config
│   └── package.json
├── .gitignore
└── README.md
```
