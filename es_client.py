import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

# =========================
# ENV CONFIG
# =========================
ES_HOST = os.getenv("ES_HOST", "https://localhost:8877")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASS", "password")
INDEX = os.getenv("ES_INDEX", "abg_data")

# =========================
# Elasticsearch Client
# =========================
es = Elasticsearch(
    [ES_HOST],
    http_auth=(ES_USER, ES_PASS),
    verify_certs=False
)

# =========================
# SERVICE GROUPS (AWS = All Services)
# =========================
SERVICE_GROUPS = ["Amazon Elastic Compute Cloud",
                  "Amazon Simple Storage Service",
                  "Amazon Relational Database Service",
                  "AWS Lambda",
                  "Amazon CloudWatch",
                  "Amazon Simple Queue Service",
                  "Amazon Glacier",
                  "Amazon Lightsail",
                  "AWS Glue"
]

# =========================
# Map name → ES value
# =========================
def map_service(service: str):
    if not service:
        return None

    service = service.upper()

    if service == "AWS":
        return SERVICE_GROUPS  # multi-service array

    lookup = {
        "EC2": "Amazon Elastic Compute Cloud",
        "S3": "Amazon Simple Storage Service",
        "RDS": "Amazon Relational Database Service",
    }
    return lookup.get(service, service)


# =========================
# COST SUMMARY
# =========================
def get_cost_summary(service: str, start_date: str, end_date: str):
    mapped = map_service(service)

    # MULTI-SERVICE MATCH
    if isinstance(mapped, list):
        must_filters = [{"terms": {"ResourceType": mapped}}]
    else:
        must_filters = [{"match": {"ResourceType": mapped}}] if mapped else []

    query = {
        "query": {
            "bool": {
                "must": must_filters + [
                    {"range": {"Timestamp": {"gte": start_date, "lte": end_date}}}
                ]
            }
        },
        "aggs": {"total_cost": {"sum": {"field": "UnBlendedCost"}}},
        "size": 0
    }

    print("📡 Running ES Query:", query)

    res = es.search(index=INDEX, body=query)
    total = res.get("aggregations", {}).get("total_cost", {}).get("value", 0)

    return {
        "type": "cost_summary",
        "service": mapped,
        "total_cost": total,
        "start": start_date,
        "end": end_date
    }


# =========================
# COST TREND
# =========================
def get_cost_trend(service: str, start_date: str, end_date: str, interval="day"):
    mapped = map_service(service)

    if isinstance(mapped, list):
        must_filters = [{"terms": {"ResourceType": mapped}}]
    else:
        must_filters = [{"match": {"ResourceType": mapped}}] if mapped else []

    query = {
        "query": {
            "bool": {
                "must": must_filters + [
                    {"range": {"Timestamp": {"gte": start_date, "lte": end_date}}}
                ]
            }
        },
        "aggs": {
            "cost_trend": {
                "date_histogram": {
                    "field": "Timestamp",
                    "calendar_interval": interval
                },
                "aggs": {"daily_cost": {"sum": {"field": "UnBlendedCost"}}}
            }
        },
        "size": 0
    }

    print("📊 Running ES Trend Query:", query)

    res = es.search(index=INDEX, body=query)

    buckets = res["aggregations"]["cost_trend"]["buckets"]

    trend = [{"date": b["key_as_string"], "cost": b["daily_cost"]["value"]} for b in buckets]

    return {
        "type": "cost_trend",
        "service": mapped,
        "data": trend,
        "start": start_date,
        "end": end_date
    }

