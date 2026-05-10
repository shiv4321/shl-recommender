import json
import requests
import re

API_URL = "https://shl-recommender-i5tl.onrender.com/chat"
TEST_CASES = [
    {
        "id": "C1 - Senior Leadership Selection",
        "messages": [
            {"role": "user", "content": "We need a solution for senior leadership. CXOs and directors, 15+ years experience. This is for selection, comparing candidates against a leadership benchmark."},
            {"role": "assistant", "content": "Got it. For senior leadership selection with a leadership benchmark, I can recommend assessments."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Occupational Personality Questionnaire OPQ32r", "OPQ Universal Competency Report 2.0", "OPQ Leadership Report"]
    },
    {
        "id": "C2 - Senior Rust Engineer",
        "messages": [
            {"role": "user", "content": "I'm hiring a senior Rust engineer for high-performance networking infrastructure. Add a cognitive test too."},
            {"role": "assistant", "content": "Understood. Senior Rust engineer with cognitive test needed."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Smart Interview Live Coding", "Linux Programming (General)", "Networking and Implementation (New)", "SHL Verify Interactive G+", "Occupational Personality Questionnaire OPQ32r"]
    },
    {
        "id": "C3 - Contact Centre Agents",
        "messages": [
            {"role": "user", "content": "We're screening 500 entry-level contact centre agents. Inbound calls, customer service focus. English US language."},
            {"role": "assistant", "content": "Got it. Entry-level contact centre, English US, high volume screening."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["SVAR - Spoken English (US)  (New)", "Contact Center Call Simulation (New)", "Entry Level Customer Serv-Retail & Contact Center", "Customer Service Phone Simulation"]
    },
    {
        "id": "C4 - Graduate Financial Analysts",
        "messages": [
            {"role": "user", "content": "Hiring graduate financial analysts, final-year students, no work experience. Need numerical reasoning, finance knowledge, and situational judgement."},
            {"role": "assistant", "content": "Understood. Graduate financial analysts needing numerical, finance, and SJT assessments."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["SHL Verify Interactive \u2013 Numerical Reasoning", "Financial Accounting (New)", "Basic Statistics (New)", "Graduate Scenarios", "Occupational Personality Questionnaire OPQ32r"]
    },
    {
        "id": "C5 - Sales Reskilling",
        "messages": [
            {"role": "user", "content": "As part of our restructuring and annual talent audit, we need to re-skill our Sales organization."},
            {"role": "assistant", "content": "Understood. Sales reskilling and talent audit for the full sales organization."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Global Skills Assessment", "Global Skills Development Report", "Occupational Personality Questionnaire OPQ32r", "OPQ MQ Sales Report", "Sales Transformation 2.0 - Individual Contributor"]
    },
    {
        "id": "C6 - Plant Operators Safety",
        "messages": [
            {"role": "user", "content": "We're hiring plant operators for a chemical facility. Safety is top priority. We are industrial classified."},
            {"role": "assistant", "content": "Understood. Industrial plant operators, safety-critical role."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Manufac. & Indust. - Safety & Dependability 8.0", "Workplace Health and Safety (New)"]
    },
    {
        "id": "C7 - Bilingual Healthcare Admin",
        "messages": [
            {"role": "user", "content": "We're hiring bilingual healthcare admin staff in South Texas. They handle patient records, need Spanish assessment, HIPAA compliance critical. They are functionally bilingual so use hybrid approach."},
            {"role": "assistant", "content": "Understood. Bilingual healthcare admin, hybrid English knowledge tests and Spanish personality assessments."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["HIPAA (Security)", "Medical Terminology (New)", "Microsoft Word 365 - Essentials (New)", "Dependability and Safety Instrument (DSI)", "Occupational Personality Questionnaire OPQ32r"]
    },
    {
        "id": "C8 - Admin Assistants Excel Word",
        "messages": [
            {"role": "user", "content": "I need to quickly screen admin assistants for Excel and Word daily use. Include simulations to capture capabilities."},
            {"role": "assistant", "content": "Understood. Admin assistants needing Excel and Word assessments including simulations."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Microsoft Excel 365 (New)", "Microsoft Word 365 (New)", "MS Excel (New)", "MS Word (New)", "Occupational Personality Questionnaire OPQ32r"]
    },
    {
        "id": "C9 - Senior Full Stack Engineer",
        "messages": [
            {"role": "user", "content": "Senior Full-Stack Engineer, backend-leaning, senior IC. Core Java advanced, Spring, SQL, AWS, Docker. Include cognitive test and personality."},
            {"role": "assistant", "content": "Understood. Senior backend engineer, Java/Spring/SQL/AWS/Docker with cognitive and personality."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["Core Java (Advanced Level) (New)", "Spring (New)", "SQL (New)", "Amazon Web Services (AWS) Development (New)", "Docker (New)", "SHL Verify Interactive G+", "Occupational Personality Questionnaire OPQ32r"]
    },
    {
        "id": "C10 - Graduate Management Trainee",
        "messages": [
            {"role": "user", "content": "We run a graduate management trainee scheme. Need cognitive and situational judgement only, no personality test."},
            {"role": "assistant", "content": "Understood. Graduate management trainees, cognitive and SJT only, no personality."},
            {"role": "user", "content": "Go ahead and recommend."}
        ],
        "expected": ["SHL Verify Interactive G+", "Graduate Scenarios"]
    },
]

with open("shl_catalog.json", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r'[\x00-\x1f\x7f]', ' ', content)
CATALOG = json.loads(content)
CATALOG_URLS = {item["link"] for item in CATALOG}


def recall_at_k(recommended, expected, k=10):
    rec_names = [r["name"] for r in recommended[:k]]
    hits = sum(1 for e in expected if any(e.lower() in r.lower() for r in rec_names))
    return hits / len(expected) if expected else 0


def run_eval():
    results = []
    for case in TEST_CASES:
        resp = requests.post(API_URL, json={"messages": case["messages"]}).json()
        recs = resp.get("recommendations", [])

        schema_ok = all("name" in r and "url" in r and "test_type" in r for r in recs)
        grounded = all(r["url"] in CATALOG_URLS for r in recs)
        recall = recall_at_k(recs, case["expected"])

        results.append({
            "test": case["id"],
            "schema_ok": schema_ok,
            "grounded": grounded,
            "recall@10": round(recall, 2),
            "num_recommendations": len(recs)
        })

        print(f"{case['id']}: schema={schema_ok} | grounded={grounded} | recall@10={recall:.2f} | recs={len(recs)}")

    mean_recall = sum(r["recall@10"] for r in results) / len(results)
    print(f"\nMean Recall@10: {mean_recall:.2f}")
    print(f"Groundedness: {sum(r['grounded'] for r in results)}/{len(results)}")
    print(f"Schema OK: {sum(r['schema_ok'] for r in results)}/{len(results)}")


if __name__ == "__main__":
    run_eval()
