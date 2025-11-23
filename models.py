from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model :str = ""



class CostSummaryData(BaseModel):
    type: Literal["cost_summary"]
    service: str
    start_date: str
    end_date: str
    total_cost: float


class CostTrendPoint(BaseModel):
    date: str
    cost: float


class CostTrendData(BaseModel):
    type: Literal["cost_trend"]
    service: str
    start_date: str
    end_date: str
    interval: str
    points: List[CostTrendPoint]


class ChatResponse(BaseModel):
    reply: str
    data: Optional[Dict[str, Any]] = None
