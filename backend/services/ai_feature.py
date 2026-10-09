import os
import json
import sys
import traceback
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(BACKEND_ENV)

api_key = os.getenv("GOOGLE_API_KEY")

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client

class ReorderInsightsResponse(BaseModel):
    urgency_explanation: str = Field(description="1-2 sentences explaining the urgency level with specific numbers.")
    demand_insight: str = Field(description="1 sentence on what the trend and standard deviation imply.")
    purchase_recommendation: str = Field(description="1 sentence with buy/delay advice, quantity, and reasoning.")
    risk_factors: list[str] = Field(description="List of 2-3 operational or financial risk factors.")
    action_items: list[str] = Field(description="List of 2-3 concrete steps for the station manager.")

def get_ai_reorder_insights(fuel_data: dict) -> dict:
    prompt = f"""
You are an expert fuel inventory advisor for a gas station in the Philippines.

Analyze the following fuel metrics and provide clear, actionable inventory advice.

METRICS:
- Fuel Type: {fuel_data['fuel_name']}
- Current Stock: {fuel_data['current_stock']}L / {fuel_data['tank_capacity']}L capacity
- Average Daily Usage: {fuel_data['avg_daily_usage']}L (Std Dev: {fuel_data['usage_std_dev']}L)
- 14-Day Trend: {fuel_data['trend']}
- Days Remaining: {fuel_data['days_remaining']} days
- Reorder Point: {fuel_data['reorder_point']}L
- Safety Stock: {fuel_data['safety_stock']}L
- Delivery Lead Time: 3 days
- Date: {date.today().isoformat()}
"""
    resp = None
    try:
        client = _get_client()
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=ReorderInsightsResponse,
            )
        )
        return json.loads(resp.text)

    except Exception as e:
        print("\n=== GEMINI CALL FAILED ===", file=sys.stderr, flush=True)
        traceback.print_exc()
        
        if resp and hasattr(resp, "text"):
            print("Response snippet:", resp.text[:300], file=sys.stderr)
        return {
            "urgency_explanation": f"Stock is at {fuel_data.get('current_stock', 0)}L relative to reorder point of {fuel_data.get('reorder_point', 0)}L.",
            "demand_insight": f"Recent 14-day trend is classified as {fuel_data.get('trend', 'unknown')}.",
            "purchase_recommendation": "Manual review required due to temporary insight service disruption.",
            "risk_factors": ["Automated AI analytics temporarily unavailable"],
            "action_items": ["Verify tank gauge levels manually", "Check pending purchase orders in system"]
        }