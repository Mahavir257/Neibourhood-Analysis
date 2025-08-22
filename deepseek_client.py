import requests

def build_prompt(location_info):
    prompt = f"""
You are a real estate neighbourhood expert.
I will give you structured data about a location.
You must create a clear scorecard and summary.

Data:
Location: {location_info['location']}
Safety Score: {location_info['safety_score']} / 10
Traffic Score: {location_info['traffic_score']} / 10
Schools: {location_info['schools']}
Hospitals: {location_info['hospitals']}
Future Growth: {location_info['future_growth']}
Average Price per Sqft: ₹{location_info['avg_price_per_sqft']}
""".strip()
    return prompt

def call_deepseek(prompt, api_key="sk-54bd3323c4d14bf08b941f0bff7a47d5"):
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']
