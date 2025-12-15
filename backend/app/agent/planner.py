import json
import google.generativeai as genai

model = genai.GenerativeModel("gemini-2.5-flash")

def plan_action(user_message: str, state: dict | None):
    prompt = f"""
You are a shopping assistant planner.

Conversation state:
{state}

User message:
"{user_message}"

Decide ONE action:
- SEARCH (new product search)
- REFINE (modify existing results)
- ASK_CLARIFICATION

Return STRICT JSON:
{{
  "action": "...",
  "parameters": {{}}
}}

Rules:
- "cheaper", "under X", "only X" → REFINE
- greetings → ASK_CLARIFICATION
- new product intent → SEARCH
- Do NOT mention system behavior
"""

    try:
        res = model.generate_content(prompt)
        return json.loads(res.text)
    except Exception:
        return {"action": "SEARCH", "parameters": {}}