from llm_client import analyze_query, ask_model
from es_client import get_cost_summary
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


# Maps short service names to actual ES field values
SERVICE_MAP = {
    "EC2": "Amazon Elastic Compute Cloud",
    "AWS": "*",
    "S3": "Amazon Simple Storage Service",
}


def resolve_dates(message: str, analysis: dict):
    now = datetime.utcnow()
    msg = message.lower()

    # Rolling window: last 30 days
    if "last 30" in msg or "past 30" in msg:
        return (
            (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            now.strftime("%Y-%m-%d"),
        )

    # Previous calendar month
    if "last month" in msg:
        first = now.replace(day=1) - relativedelta(months=1)
        last = first + relativedelta(day=31)
        return first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")

    # If LLM provided actual dates, trust them only if not None
    start = analysis.get("start_date")
    end = analysis.get("end_date")

    if start and end and start != "None" and end != "None":
        return start, end

    # FINAL FALLBACK — dataset is Oct 2025
    return "2025-10-01", "2025-10-31"


async def process_query(data):
    message = data.message
    model = data.model

    analysis = analyze_query(data)

    intent = analysis.get("intent")

    # 1️⃣ Handle cost summary queries
    if intent == "COST_SUMMARY":
        service = analysis.get("service")
        start, end = resolve_dates(message, analysis)

        data = get_cost_summary(service, start, end)

        summary = ask_model(
            prompt=f"User asked: {message}\nHere is extracted cost summary data:\n{data}",
            system_prompt="Respond concisely with a business-friendly cost summary.",
            model=model,
        )

        return {"reply": summary, "raw": data}

    # 2️⃣ Handle general messages gracefully
    if intent == "UNKNOWN" or intent is None:
        reply = ask_model(
            model=model,
            prompt=message,
            system_prompt="You are a FinOps assistant. Respond conversationally. If the query seems cost-related, ask a clarifying question like 'Which service?'",
        )
        return {"reply": reply, "raw": None}

    # 3️⃣ Fallback behavior
    reply = ask_model(
        model=model,
        prompt=message,
        system_prompt="Respond as a FinOps assistant in a helpful conversational way.",
    )
    return {"reply": reply, "raw": None}
