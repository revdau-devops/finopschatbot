import json
import requests
from model_config import model_config


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            lines = lines[1:-1]
        text = "\n".join(lines).strip()
    return text


def ask_model(model: str, prompt: str, system_prompt: str | None = None) -> str:
    """
    Send prompt to Ollama and return string output.
    """
    model_data = model_config(model=model)
    HOST = model_data.get("api_host")
    API_KEY = model_data.get("api_key")
    MODEL = model_data.get("model")

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [], "stream": False}

    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})

    payload["messages"].append({"role": "user", "content": prompt})

    res = requests.post(HOST, json=payload, headers=headers)
    res.raise_for_status()

    data = res.json()
    try:
        return data["message"]["content"]
    except:
        return data["choices"][0]["message"]["content"]


def analyze_query(data) -> dict:
    """
    Convert user input → structured intent JSON.
    """
    SYSTEM = """
You are a FinOps cloud cost assistant.

Return ONLY JSON in this format:

{
  "intent": "COST_SUMMARY" | "COST_TREND" | "EXPLANATION" | "UNKNOWN",
  "service": string or null,
  "start_date": null,
  "end_date": null,
  "interval": "day" | "week" | "month" | null
}

Rules:
- Do NOT guess dates.
- If the user asks for "last month", "this quarter", "last 30 days" → return start_date and end_date as null.
- Backend will calculate actual dates.
- service should be short like "EC2" not full sentence.
- Output only JSON, no text.
"""

    raw = ask_model(model=data.model, prompt=data.message, system_prompt=SYSTEM)
    cleaned = _strip_code_fences(raw)

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("❌ FAILED JSON:", cleaned)
        return {"intent": "UNKNOWN"}
