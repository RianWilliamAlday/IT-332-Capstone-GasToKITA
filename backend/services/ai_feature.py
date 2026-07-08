import google.generativeai as genai
import os
import json
from typing import List, Dict
from datetime import date, timedelta

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        "temperature": 0.2,
        "response_mime_type": "application/json"
    }
)

def get_ai_reorder_insights(fuel_data: Dict) -> Dict:
    """
    fuel_data = calculated stats from your existing endpoint
    AI adds reasoning + recommendations in natural language
    """

    prompt = f"""
You are a fuel inventory advisor for a gas station in the Philippines.

Analyze this fuel data and provide actionable insights.

DATA:
Fuel: {fuel_data['fuel_name']}
Current Stock: {fuel_data['current_stock']}L / {fuel_data['tank_capacity']}L capacity
Average Daily Usage: {fuel_data['avg_daily_usage']}L (std dev: {fuel_data['usage_std_dev']}L)
Trend: {fuel_data['trend']} over last 14 days
Days Remaining: {fuel_data['days_remaining']}
Reorder Point: {fuel_data['reorder_point']}L
Safety Stock: {fuel_data['safety_stock']}L
Lead Time: 3 days
Current Date: {date.today().isoformat()}

CONTEXT:
- This is a provincial gas station. Demand spikes during harvest season, holidays, and weekends.
- Overstocking ties up cash. Understocking means lost sales.
- Typhoon season affects deliveries.

TASK:
Return JSON with these exact keys:
{{
  "urgency_explanation": "1-2 sentences why this urgency level. Mention specific numbers.",
  "demand_insight": "1 sentence on what the trend + std_dev means for this fuel.",
  "purchase_recommendation": "1 sentence: buy/delay + quantity + reasoning",
  "risk_factors": ["list", "of", "2-3 risks"],
  "action_items": ["list", "of", "2-3 concrete steps for manager"]
}}

Rules:
- Be concise. No fluff.
- Use the numbers provided. Do NOT invent new numbers.
- If overstocked, explain cash impact.
- If critical, be direct.
"""

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {
            "urgency_explanation": f"Stock at {fuel_data['current_stock']}L vs reorder point {fuel_data['reorder_point']}L",
            "demand_insight": f"Trend is {fuel_data['trend']}",
            "purchase_recommendation": "Review metrics manually",
            "risk_factors": ["AI analysis unavailable"],
            "action_items": ["Check dashboard"]
        }