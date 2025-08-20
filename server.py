from flask import Flask, request, jsonify
import json
import pandas as pd
from copy import deepcopy
from deepseek_client import build_prompt, call_deepseek

app = Flask(__name__)

# Load neighborhood data from JSON file
with open("neighbourhood_data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# Convert JSON data to DataFrame for processing and scoring
DF = pd.DataFrame(DATA)

# Compute education + health rating normalized from 0 to 10
max_sum = (DF["schools"] + DF["hospitals"]).max()
DF["edu_health_rating"] = ((DF["schools"] + DF["hospitals"]) / max_sum * 10).round(1)

# Map growth categories to numeric scores
growth_map = {"High": 10, "Medium": 6.5, "Low": 3}
DF["growth_score"] = DF["future_growth"].map(growth_map).fillna(5)

# Compute price affordability score where lower price gets higher score (0-10 scale)
max_p = DF["avg_price_per_sqft"].max()
min_p = DF["avg_price_per_sqft"].min()
rng = max(1, max_p - min_p)
DF["price_afford_score"] = ((max_p - DF["avg_price_per_sqft"]) / rng * 10).round(2)


@app.get("/locations")
def list_locations():
    """ List all available location names sorted alphabetically """
    return jsonify(sorted([d["location"] for d in DATA]))


@app.get("/location")
def get_location():
    """ Get detailed information for a single location with computed scores """
    name = request.args.get("name", "")
    item = next((x for x in DATA if x["location"].lower() == name.lower()), None)
    if not item:
        return jsonify({"error": "Location not found"}), 404
    
    # Create a copy to avoid side-effects on global DATA
    item_copy = deepcopy(item)
    row = DF[DF["location"].str.lower() == name.lower()].iloc[0].to_dict()
    
    item_copy.update({
        "edu_health_rating": row["edu_health_rating"],
        "growth_score": row["growth_score"],
        "price_afford_score": row["price_afford_score"]
    })
    return jsonify(item_copy)


@app.post("/top-picks")
def top_picks():
    """ Return top recommended locations based on user filters and weighted scoring """
    body = request.get_json(force=True)
    params = {
        "min_safety": float(body.get("min_safety", 0)),
        "max_traffic": float(body.get("max_traffic", 10)),
        "growth": body.get("growth", "Any"),
        "max_price": float(body.get("max_price", DF["avg_price_per_sqft"].max())),
        "top_n": int(body.get("top_n", 5)),
        "weights": body.get("weights", {"safety": 0.3, "edu": 0.25, "traffic": 0.15, "price": 0.15, "growth": 0.15}),
        "city_filter": body.get("city_filter", [])
    }

    df = DF.copy()
    if params["city_filter"]:
        pattern = "|".join(params["city_filter"])
        df = df[df["location"].str.contains(pattern, case=False)]

    df = df[
        (df["safety_score"] >= params["min_safety"]) &
        (df["traffic_score"] <= params["max_traffic"]) &
        (df["avg_price_per_sqft"] <= params["max_price"])
    ]

    if params["growth"] != "Any":
        df = df[df["future_growth"] == params["growth"]]

    w = params["weights"]
    total_w = sum([w.get("safety", 0), w.get("edu", 0), w.get("traffic", 0), w.get("price", 0), w.get("growth", 0)])
    if total_w == 0:
        return jsonify({"error": "Total weight cannot be zero"}), 400

    ws = w.get("safety", 0) / total_w
    we = w.get("edu", 0) / total_w
    wt = w.get("traffic", 0) / total_w
    wp = w.get("price", 0) / total_w
    wg = w.get("growth", 0) / total_w

    df = df.copy()
    df["composite_score"] = (
        ws * df["safety_score"] +
        we * df["edu_health_rating"] +
        wp * df["price_afford_score"] +
        wg * df["growth_score"] -
        wt * df["traffic_score"]
    ).round(3)

    out = df.sort_values("composite_score", ascending=False).head(params["top_n"])[[
        "location", "composite_score", "safety_score", "traffic_score", "edu_health_rating", "future_growth", "avg_price_per_sqft", "price_afford_score", "growth_score"
    ]]
    return out.to_json(orient="records")


@app.post("/analyze")
def analyze():
    """ Generate AI-based analysis for a given location using DeepSeek """
    body = request.get_json(force=True)
    name = body.get("location", "")
    item = next((x for x in DATA if x["location"].lower() == name.lower()), None)
    if not item:
        return jsonify({"error": "Location not found"}), 404
    
    prompt = build_prompt(item)
    result = call_deepseek(prompt)
    return jsonify({"analysis": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
