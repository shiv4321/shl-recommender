# Assessment Recommender

A conversational AI agent that helps hiring managers find the right  assessments through dialogue.

---

## What It Does

Takes a hiring manager from a vague intent ("I am hiring a Java developer") to a grounded shortlist of assessments through multi-turn conversation.

- Clarifies vague queries before recommending
- Recommends 1 to 10 assessments once it has enough context
- Refines recommendations when the user changes constraints
- Compares assessments using only catalog data
- Refuses off-topic requests (legal advice, general hiring, prompt injection)
- Never returns a URL that is not in the scraped catalog

---

## API

### GET /health
Returns `{"status": "ok"}` with HTTP 200.

### POST /chat

Request:
```json
{
  "messages": [
    {"role": "user", "content": "I am hiring a Java developer"},
    {"role": "assistant", "content": "What seniority level are you hiring for?"},
    {"role": "user", "content": "Mid-level, around 4 years"}
  ]
}
```

Response:
```json
{
  "reply": "Here are assessments that fit a mid-level Java developer.",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/...", "test_type": "K"},
    {"name": "OPQ Profile Report", "url": "https://www.shl.com/...", "test_type": "P"}
  ],
  "end_of_conversation": false
}
```

The API is stateless. Every call carries the full conversation history. No per-conversation state is stored server-side.

---

## Stack

| Component | Tool |
|---|---|
| Web scraping | requests + BeautifulSoup |
| Catalog storage | JSON (377 assessments) |
| LLM | GPT-4o-mini via OpenAI API |
| API framework | FastAPI + Uvicorn |
| Deployment | Render |

---

## Project Structure

```
shl-recommender/
├── main.py            # FastAPI app with /health and /chat endpoints
├── scrape.py          # Catalog scraper (Individual Test Solutions only)
├── shl_catalog.json   # Scraped catalog (377 assessments)
├── requirements.txt   # Python dependencies
└── .env               # API keys (not committed)
```

---

## How the Catalog Was Built

`scrape.py` paginates through the Individual Test Solutions section of the SHL product catalog at 12 items per page across 32 pages. For each assessment it extracts the name, URL, test type codes, remote testing availability, and adaptive/IRT flag. The result is 377 assessments saved to `shl_catalog.json`.

---

## How the Agent Works

The full catalog is embedded into the system prompt as a structured text block. The LLM is instructed to respond only in a strict JSON format containing `reply`, `recommendations`, and `end_of_conversation`. A regex extraction step handles cases where the model adds text outside the JSON block before parsing.

The system prompt enforces four behaviors:

1. Ask clarifying questions for vague queries before recommending
2. Recommend only from the catalog once enough context is gathered
3. Update recommendations when the user refines constraints
4. Refuse anything outside assessment selection

---

## Running Locally

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

Test:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"I need an assessment for a Java developer"}]}'
```

---

## Requirements

```
fastapi
uvicorn
openai
python-dotenv
pydantic
```
