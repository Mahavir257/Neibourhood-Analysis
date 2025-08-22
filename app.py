import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from deepseek_client import build_prompt, call_deepseek
import io

# Enhanced neighborhood analysis tool with additional features

st.set_page_config(page_title="Ahmedabad-Gandhinagar Neighbourhood PRO", page_icon="🏙️", layout="wide")

def extract_dist(row, key):
    d = row.get(key, {})
    return d.get("distance_km") if isinstance(d, dict) else None

@st.cache_data
def load_data():
    with open("neighbourhood_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    max_sum = (df["schools"] + df["hospitals"]).max()
    df["edu_health_rating"] = ((df["schools"] + df["hospitals"]) / max_sum * 10).round(1)
    growth_map = {"High": 10, "Medium": 6.5, "Low": 3}
    df["growth_score"] = df["future_growth"].map(growth_map).fillna(5)
    max_p = df["avg_price_per_sqft"].max()
    min_p = df["avg_price_per_sqft"].min()
    rng = max(1, max_p - min_p)
    df["price_afford_score"] = ((max_p - df["avg_price_per_sqft"]) / rng * 10).round(2)
    df["airport_km"] = df.apply(lambda r: extract_dist(r, "nearest_airport"), axis=1)
    df["metro_km"] = df.apply(lambda r: extract_dist(r, "metro") if r.get("metro", {}).get("available", False) else None, axis=1)
    return df

df = load_data()
st.title("Ahmedabad–Gandhinagar Neighbourhood Intelligence PRO Tool")

# --- COMPARISON UI --- #
st.header("1️⃣ Area-wise Connectivity Comparison")
comp_chart_df = df[["location", "airport_km", "metro_km"]]

fig = go.Figure([
    go.Bar(name='Airport (km)', x=comp_chart_df["location"], y=comp_chart_df["airport_km"]),
    go.Bar(name='Metro (km)', x=comp_chart_df["location"], y=comp_chart_df["metro_km"])
])
fig.update_layout(barmode='group', xaxis_tickangle=-45, title="Distance from Airport & Metro", height=600)
st.plotly_chart(fig, use_container_width=True)

# --- FULL TABLE and EXPORT --- #
st.header("2️⃣ Compare All Areas (Data Table & Export)")
comp_table = df[["location", "safety_score", "edu_health_rating", "traffic_score", "future_growth", "avg_price_per_sqft", "airport_km", "metro_km"]]
st.dataframe(comp_table, use_container_width=True)

excel_buff = io.BytesIO()
with pd.ExcelWriter(excel_buff, engine='xlsxwriter') as writer:
    comp_table.to_excel(writer, index=False, sheet_name='Areas')
st.download_button(
    label="⬇️ Download All Area Comparison (Excel)",
    data=excel_buff.getvalue(),
    file_name="all_area_comparison.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- RADAR CHART MULTIAREA --- #
st.header("3️⃣ Multi-Area Radar Chart")
radar_choices = st.multiselect("Select up to 5 localities:", df["location"], default=df["location"].tolist()[:3])
if len(radar_choices) >= 2:
    radar_df = df[df["location"].isin(radar_choices)].set_index("location")[["safety_score", "edu_health_rating", "traffic_score", "airport_km", "metro_km"]]
    fig2 = go.Figure()
    for area in radar_df.index:
        vals = radar_df.loc[area].tolist()
        fig2.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=radar_df.columns.tolist() + [radar_df.columns], fill='toself', name=area))
    fig2.update_layout(title="Side-by-side Locality Radar Comparison", polar=dict(radialaxis=dict(visible=True)))
    st.plotly_chart(fig2, use_container_width=True)

# --- AI PRO BEST BUY REPORT (DeepSeek) --- #
st.header("4️⃣ PRO Best-Buy AI Analysis & Download")
if st.button("Generate PRO Best-Buy Report (AI)"):
    prompt = "You are a senior real estate consultant. Given this Ahmedabad and Gandhinagar area table:\n"
    for i, row in comp_table.iterrows():
        prompt += f"- {row['location']}: Safety={row['safety_score']}, Edu/Health={row['edu_health_rating']}, Traffic={row['traffic_score']}, Price={row['avg_price_per_sqft']}, Airport={row['airport_km']}km, Metro={row['metro_km']}km, Growth={row['future_growth']}\n"
    prompt += "\nWrite a PRO-level short-list of the 3 best areas for a buyer seeking balance, plus a concise summary table as markdown, and a crisp tip for investors vs families."
    try:
        ai_report = call_deepseek(prompt)
        st.markdown(ai_report)
        st.download_button(
            label="⬇️ Download PRO AI Report (Markdown)",
            data=ai_report.encode('utf-8'),
            file_name="best_buy_ai_report.md",
            mime="text/markdown"
        )
    except Exception as e:
        st.error(f"AI Report failed: {e}")

# --- INDIVIDUAL AREA DEEPSEEK (OPTIONAL) --- #
st.header("5️⃣ Individual Locality AI Report (DeepSeek)")
selected = st.selectbox("Choose area:", df["location"].tolist(), index=0)
loc_row = df[df["location"] == selected].iloc[0].to_dict()
if st.button("AI Scorecard This Area"):
    loc_payload = {
        "location": loc_row["location"],
        "safety_score": int(loc_row["safety_score"]),
        "traffic_score": int(loc_row["traffic_score"]),
        "schools": int(loc_row["schools"]),
        "hospitals": int(loc_row["hospitals"]),
        "future_growth": loc_row["future_growth"],
        "avg_price_per_sqft": int(loc_row["avg_price_per_sqft"]),
    }
    prompt = build_prompt(loc_payload)
    try:
        report = call_deepseek(prompt)
        st.markdown(report)
    except Exception as e:
        st.error(f"DeepSeek call failed: {e}")

st.info("This PRO app lets you compare all localities on transit, price and AI analysis. Download summary Excel or AI report easily. Hosted 100% in the cloud for you.")
