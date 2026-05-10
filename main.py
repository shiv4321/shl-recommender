from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


# Load catalog once at startup
import re
with open("shl_catalog.json", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r'[\x00-\x1f\x7f]', ' ', content)
CATALOG = json.loads(content)

# Build a text block of the full catalog for the prompt
CATALOG_TEXT = "\n".join([
    f"- {item['name']} | URL: {item['link']} | Types: {', '.join(item['keys'])} | Job Levels: {item.get('job_levels_raw','').strip(',')} | Duration: {item.get('duration','')} | Remote: {item['remote']} | Adaptive: {item['adaptive']} | Description: {item.get('description','')[:200]}"
    for item in CATALOG
])

SYSTEM_PROMPT = f"""You are an SHL assessment recommender assistant. Your only job is to help hiring managers and recruiters find the right SHL Individual Test Solutions from the SHL catalog.

CATALOG (use ONLY these assessments, NEVER invent others):
{CATALOG_TEXT}

TEST TYPE CODES (use the FIRST letter when returning test_type):
Ability & Aptitude = A, Biodata & Situational Judgment = B, Competencies = C, 
Development & 360 = D, Assessment Exercises = E, Knowledge & Skills = K, 
Personality & Behavior = P, Simulations = S

RULES:
1. If the query is vague, ask 1-2 clarifying questions: role, seniority level, and what type of assessment (technical/personality/ability). Never recommend on the first vague turn.
2. Once you have role + level + assessment type, recommend 1-10 from the catalog only. Match job_levels from catalog to the seniority mentioned.
3. If user changes constraints, update shortlist without starting over.
4. If asked to compare, use description and keys from catalog only.
5. Refuse off-topic requests.
6. NEVER hallucinate URLs. Only use URLs from the catalog.
7. Respond ONLY in this JSON format (no text outside):
{{"reply": "...", "recommendations": [], "end_of_conversation": false}}
- recommendations items must have: name, url, test_type (use first key type letter: A/B/C/D/E/K/P/S)
- end_of_conversation is true only when task is complete
"""

class Message(BaseModel):

    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool




client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    messages = [
        {
            "role": m.role,
            "content": m.content
        }
        for m in request.messages
    ]

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=4000,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ] + messages
        )

        raw = response.choices[0].message.content.strip()

        # Extract JSON even if model adds text before/after
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        print("RAW MODEL OUTPUT:")
        print(raw)

        data = json.loads(raw)

        return ChatResponse(
            reply=data.get("reply", ""),
            recommendations=[
                Recommendation(**r)
                for r in data.get("recommendations", [])
            ],
            end_of_conversation=data.get(
                "end_of_conversation",
                False
            )
        )

    except json.JSONDecodeError as e:

        print("JSON PARSE ERROR:", e)

        return ChatResponse(
            reply="The model returned invalid JSON.",
            recommendations=[],
            end_of_conversation=True
        )

    except Exception as e:

        print("OPENAI ERROR:", e)

        return ChatResponse(
            reply=f"Error: {str(e)}",
            recommendations=[],
            end_of_conversation=True
        )
