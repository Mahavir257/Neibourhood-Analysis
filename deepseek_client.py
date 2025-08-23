import os
import requests
from typing import List, Dict, Optional
try:
	from dotenv import load_dotenv  # Optional; used if present
	load_dotenv()
except Exception:
	# If python-dotenv is not installed or fails, ignore gracefully
	pass


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


def _get_api_key(explicit_key: Optional[str] = None) -> str:
	api_key = explicit_key or os.getenv("DEEPSEEK_API_KEY", "").strip()
	if not api_key:
		raise RuntimeError("Missing DEEPSEEK_API_KEY environment variable. Set it to your DeepSeek API key.")
	return api_key


def call_deepseek_chat(messages: List[Dict[str, str]], system: Optional[str] = None, api_key: Optional[str] = None, model: str = "deepseek-chat") -> str:
	"""Call DeepSeek with multi-turn chat messages.

	messages: list like [{"role": "user"|"assistant"|"system", "content": "..."}, ...]
	system: optional system instruction; if provided, it is prepended.
	"""
	key = _get_api_key(api_key)
	url = "https://api.deepseek.com/chat/completions"
	headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
	payload_msgs = []
	if system:
		payload_msgs.append({"role": "system", "content": system})
	payload_msgs.extend(messages)
	payload = {"model": model, "messages": payload_msgs}
	response = requests.post(url, headers=headers, json=payload)
	response.raise_for_status()
	return response.json()["choices"][0]["message"]["content"]


def call_deepseek(prompt: str, api_key: Optional[str] = None, model: str = "deepseek-chat") -> str:
	"""Backward-compatible single-prompt call (wraps chat API)."""
	return call_deepseek_chat(messages=[{"role": "user", "content": prompt}], api_key=api_key, model=model)
