# API Architecture (Conceptual Design)

## Disclaimer

This is a **conceptual design document**, not an implementation.

Why? Because this is a personal learning tool designed to run locally. Turning it into a cloud API service would be like binding a bicycle to a fish - technically possible, unnecessary, and missing the point.

That said, in case it's useful, here is a approach.

## Why This Probably Shouldn't Be an API

**This application is designed for**:
- Personal use with your own text library
- Local database with your learning history
- Privacy (your vocabulary data stays on your machine)
- Customization (modify code to fit your needs)

**Making it an API would require**:
- Hosting infrastructure and costs
- User authentication and data isolation
- Privacy concerns (uploading your reading library?)
- Complexity that doesn't add value

**Better model**: Desktop/local tool (like Anki or Obsidian)
- Users run it locally
- Users control their data
- Users can modify/extend as needed

## But If We Had To...

### High-Level Architecture

```
┌─────────────┐
│   Client    │
│  (Browser,  │
│   Mobile)   │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│   FastAPI   │
│  REST API   │
└──────┬──────┘
       │
       ├─────────┐
       ▼         ▼
┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │
│(User DB) │ │ (Cache)  │
└──────────┘ └──────────┘
       │
       ▼
┌─────────────┐
│External APIs│
│ DeepL/Claude│
└─────────────┘
```

### Core Endpoints

#### Translation Service
```http
POST /api/v1/translate
Content-Type: application/json
Authorization: Bearer <token>

{
  "text": "我在学习西班牙语",
  "target_languages": ["es", "fr"],
  "comparison_mode": true
}

Response 200:
{
  "translations": {
    "en": {
      "google": "I am learning Spanish",
      "deepl": "I'm learning Spanish"
    },
    "es": {
      "google": "Estoy aprendiendo español",
      "deepl": "Estoy aprendiendo español"
    }
  },
  "cost": 0.002  // API usage cost in USD
}
```

#### Vocabulary Management
```http
POST /api/v1/vocabulary
Authorization: Bearer <token>

{
  "word": "hablar",
  "language": "es",
  "sentence": "Estoy hablando con María",
  "translations": { ... }
}

GET /api/v1/vocabulary?language=es&sort_by=last_encounter

DELETE /api/v1/vocabulary/{word_id}
```

#### AI Features (Agentic)
```http
POST /api/v1/ai/analyze
Authorization: Bearer <token>

{
  "word": "hablando",
  "language": "es",
  "context": ["sentence1", "sentence2"]
}

Response 200:
{
  "analysis": {
    "parent_suggestions": [
      {
        "word": "hablar",
        "reason": "Infinitive form of the verb",
        "confidence": 0.95
      }
    ],
    "generated_note": "Present progressive gerund (-ando form)",
    "learning_strategy": "Compare with other -ar verb conjugations"
  },
  "cost": 0.01  // Claude API call cost
}
```

### Implementation Stack

**Framework**: FastAPI
- Async support (important for multiple API calls)
- Auto-generated OpenAPI docs
- Type hints and validation (Pydantic)

**Database**: PostgreSQL
- User accounts and isolation
- Vocabulary storage
- Encounter history

**Caching**: Redis
- Cache translation results
- Rate limiting
- Session management

**Authentication**: JWT
```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
```

**Deployment**: Docker + Railway/Fly.io
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Agentic API Concepts

This is where it gets interesting. How could agentic AI principles improve API architecture?

### 1. Self-Monitoring with ReAct Framework

Traditional approach:
```python
@app.post("/api/translate")
def translate(text: str):
    return call_deepl(text)  # Hope it works
```

Agentic approach:
```python
@app.post("/api/translate")
async def translate(text: str):
    # Thought: What's the best translation engine for this text?
    analysis = await agent.analyze_request(text)
    
    # Action: Try primary engine
    result = await call_deepl(text)
    
    # Observation: Did it work? Is quality good?
    if not agent.validate_result(result):
        # Action: Try fallback
        result = await call_google(text)
    
    return result
```

**Benefit**: Self-healing API that adapts to failures

### 2. Hierarchical Error Handling (LATS-inspired)

```python
# Level 1: Detect error
if response.status_code != 200:
    
    # Level 2: Classify error type
    error_type = classify_error(response)
    
    # Level 3: Diagnose root cause
    if error_type == "rate_limit":
        diagnosis = "Too many requests"
    elif error_type == "auth":
        diagnosis = "API key expired"
    
    # Level 4: Take corrective action
    if diagnosis == "rate_limit":
        await asyncio.sleep(calculate_backoff())
        return retry_request()
    elif diagnosis == "auth":
        await refresh_api_key()
        return retry_request()
```

**Benefit**: Autonomous error recovery

### 3. Multi-Agent Optimization

```python
class TranslationAgent:
    async def optimize_engine_selection(self, text: str):
        # Agent 1: Analyze text characteristics
        features = await self.analyze_text(text)
        
        # Agent 2: Historical performance data
        stats = await self.get_engine_stats()
        
        # Agent 3: Cost analysis
        costs = await self.compare_costs()
        
        # Meta-agent: Decide optimal engine
        return self.select_best_engine(features, stats, costs)
```

**Benefit**: Autonomous optimization without human tuning

## Code Structure (if implemented)

```
api/
├── main.py                 # FastAPI app
├── routers/
│   ├── auth.py            # Authentication endpoints
│   ├── translate.py       # Translation endpoints
│   ├── vocabulary.py      # Vocabulary management
│   └── ai.py              # Agentic AI features
├── agents/
│   ├── react_agent.py     # ReAct framework implementation
│   ├── lats_agent.py      # Hierarchical error handling
│   └── optimizer.py       # Multi-agent optimization
├── models/
│   ├── user.py            # User model (Pydantic + SQLAlchemy)
│   ├── vocabulary.py      # Vocabulary model
│   └── schemas.py         # API request/response schemas
├── services/
│   ├── translation.py     # Translation service
│   ├── ai_analysis.py     # AI features
│   └── external_apis.py   # Third-party API wrappers
└── tests/
    └── ...
```

## Why This Design Makes Sense (For API Development)

Even though this specific application doesn't need to be an API, the design demonstrates understanding of:

1. **RESTful principles**: Resource-based endpoints, proper HTTP methods
2. **Authentication/Authorization**: JWT, user isolation
3. **Scalability**: Async operations, caching, database design
4. **Error handling**: Graceful degradation, retries
5. **Documentation**: OpenAPI/Swagger auto-generated
6. **Cost awareness**: Tracking API usage and costs
7. **Agentic thinking**: Self-monitoring, autonomous optimization

## Alternative: Local-First Architecture

What I would actually continue with this project:

**Model**: Anki/Obsidian style
- Desktop app (Electron or Tauri)
- Local database (SQLite)
- Optional cloud sync (user-controlled)
- Plugin system for extensions

**Benefits**:
- No server costs
- Complete privacy
- Works offline
- Users own their data
- Easy to customize

**API role**: Optional sync service
- Encrypt data before upload
- User brings their own API keys
- Minimal server logic

## Conclusion

The best architecture depends on the use case:
- Personal learning tool? → Local application
- Team collaboration? → Maybe an API
- Commercial SaaS? → Definitely an API (with proper infrastructure)

For this project: Local tool with optional cloud features is the right choice.

## References

- FastAPI documentation: https://fastapi.tiangolo.com/
- RESTful API design: https://restfulapi.net/
- Agentic API concepts: See accompanying PDF on agentic AI architectures

---


