"""
Enhanced Streamlit Web Interface for Neighborhood Analysis Tool
Modern, interactive dashboard with comprehensive real estate analysis features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import requests
from typing import Dict, List
import logging
from datetime import datetime

# Import our enhanced modules
from app import (
    get_neighborhood_info, get_investment_analysis, compare_locations,
    get_top_locations, export_analysis_report, analyzer
)
from deepseek_client import (
    call_deepseek, get_deepseek_scorecard, get_comparative_analysis,
    get_market_insights, get_investment_strategy, get_api_stats
)

# Configure page
st.set_page_config(
    page_title="🏘️ Smart Neighborhood Analysis Tool",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load neighborhood data with caching"""
    try:
        with open('neighbourhood_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Initialize session state
if 'selected_locations' not in st.session_state:
    st.session_state.selected_locations = []

if 'comparison_data' not in st.session_state:
    st.session_state.comparison_data = None

# Sidebar navigation
st.sidebar.title("🏘️ Navigation")
page = st.sidebar.selectbox(
    "Choose a feature:",
    [
        "🏠 Home Dashboard",
        "🔍 Location Explorer",
        "💰 Investment Analysis",
        "⚖️ Location Comparison",
        "📊 Market Insights",
        "🤖 AI Analysis",
        "📈 Top Picks",
        "📋 Export Reports",
        "⚙️ Settings"
    ]
)

# Load data
df = load_data()

if df.empty:
    st.error("❌ No data available. Please check the data file.")
    st.stop()

# Main content based on selected page
if page == "🏠 Home Dashboard":
    st.markdown('<h1 class="main-header">🏘️ Smart Neighborhood Analysis Tool</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the most comprehensive real estate analysis platform for Ahmedabad & Gandhinagar! 🏙️
    
    **What can you do here?**
    - 🔍 **Explore Locations**: Get detailed insights on any neighborhood
    - 💰 **Investment Analysis**: Calculate ROI, risks, and returns
    - ⚖️ **Compare Areas**: Side-by-side comparison of multiple locations
    - 🤖 **AI Insights**: Get AI-powered market analysis and recommendations
    - 📊 **Market Trends**: Understand current market dynamics
    - 📋 **Export Reports**: Generate comprehensive analysis reports
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📍 Total Locations",
            value=len(df),
            delta=f"{df['city'].nunique()} Cities"
        )
    
    with col2:
        avg_price = df['avg_price_per_sqft'].mean()
        st.metric(
            label="💰 Avg Price/sq ft",
            value=f"₹{avg_price:,.0f}",
            delta=f"Range: ₹{df['avg_price_per_sqft'].min():,.0f} - ₹{df['avg_price_per_sqft'].max():,.0f}"
        )
    
    with col3:
        avg_safety = df['safety_score'].mean()
        st.metric(
            label="🛡️ Avg Safety Score",
            value=f"{avg_safety:.1f}/10",
            delta=f"Top: {df['safety_score'].max()}/10"
        )
    
    with col4:
        high_growth = len(df[df['future_growth'] == 'High'])
        st.metric(
            label="📈 High Growth Areas",
            value=high_growth,
            delta=f"{(high_growth/len(df)*100):.1f}% of total"
        )
    
    # Interactive charts
    st.subheader("📊 Market Overview")
    
    # Price distribution by city
    fig_price = px.box(
        df, 
        x='city', 
        y='avg_price_per_sqft',
        title="Price Distribution by City",
        color='city',
        labels={'avg_price_per_sqft': 'Price per Sq Ft (₹)', 'city': 'City'}
    )
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Safety vs Investment Score scatter
    fig_scatter = px.scatter(
        df,
        x='safety_score',
        y='investment_score',
        size='schools',
        color='future_growth',
        hover_name='location',
        hover_data=['avg_price_per_sqft', 'rental_yield'],
        title="Safety vs Investment Score (Size: Number of Schools)",
        labels={'safety_score': 'Safety Score', 'investment_score': 'Investment Score'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

elif page == "🔍 Location Explorer":
    st.header("🔍 Location Explorer")
    
    # Location selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        locations = df['location'].tolist()
        selected_location = st.selectbox(
            "🏘️ Select a location to explore:",
            options=locations,
            index=0
        )
    
    with col2:
        st.info("💡 **Tip**: Use the dropdown to explore detailed information about any neighborhood.")
    
    if selected_location:
        # Get location info
        location_info = get_neighborhood_info(selected_location)
        
        if 'error' not in location_info:
            # Location header
            st.subheader(f"📍 {location_info['location']}")
            
            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                safety_score = location_info.get('safety_score', 0)
                st.metric("🛡️ Safety", f"{safety_score}/10", 
                         delta="Excellent" if safety_score >= 9 else "Good" if safety_score >= 7 else "Average")
            
            with col2:
                price = location_info.get('avg_price_per_sqft', 0)
                st.metric("💰 Price/sq ft", f"₹{price:,}")
            
            with col3:
                growth = location_info.get('future_growth', 'N/A')
                st.metric("📈 Growth", growth)
            
            with col4:
                schools = location_info.get('schools', 0)
                st.metric("🏫 Schools", schools)
            
            with col5:
                connectivity = location_info.get('connectivity_score', 0)
                st.metric("🚊 Connectivity", f"{connectivity}/10")
            
            # Detailed information tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Scores & Ratings", "🏗️ Infrastructure", "🎯 Amenities", "🚗 Transportation"])
            
            with tab1:
                # Scores radar chart
                scores = {
                    'Safety': location_info.get('safety_score', 0),
                    'Infrastructure': location_info.get('infrastructure_score', 0),
                    'Lifestyle': location_info.get('lifestyle_score', 0),
                    'Environment': location_info.get('environment_score', 0),
                    'Connectivity': location_info.get('connectivity_score', 0),
                    'Investment': location_info.get('investment_score', 0)
                }
                
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(scores.values()),
                    theta=list(scores.keys()),
                    fill='toself',
                    name=selected_location,
                    line_color='rgb(31, 119, 180)'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )
                    ),
                    title="📊 Location Score Profile",
                    showlegend=False
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🏥 Healthcare Facilities**")
                    st.write(f"• Hospitals: {location_info.get('hospitals', 'N/A')}")
                    
                    st.write("**🏫 Education**")
                    st.write(f"• Schools: {location_info.get('schools', 'N/A')}")
                    
                    st.write("**👮 Safety & Security**")
                    police = location_info.get('police_station', {})
                    if police:
                        st.write(f"• {police.get('name', 'Police Station')}")
                        st.write(f"• Distance: {police.get('distance_km', 'N/A')} km")
                
                with col2:
                    st.write("**📊 Demographics**")
                    if location_info.get('population'):
                        st.write(f"• Population: {location_info['population']:,}")
                    if location_info.get('population_density'):
                        st.write(f"• Density: {location_info['population_density']:,}/sq km")
                    
                    st.write("**🏢 Infrastructure Score**")
                    infra_score = location_info.get('infrastructure_score', 0)
                    st.progress(infra_score / 10, text=f"{infra_score}/10")
            
            with tab3:
                amenities = location_info.get('amenities', {})
                if amenities:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'malls' in amenities and amenities['malls']:
                            st.write("**🛒 Shopping Centers**")
                            for mall in amenities['malls']:
                                st.write(f"• {mall}")
                        
                        if 'parks' in amenities and amenities['parks']:
                            st.write("**🌳 Parks & Recreation**")
                            for park in amenities['parks']:
                                st.write(f"• {park}")
                    
                    with col2:
                        if 'restaurants' in amenities:
                            st.write(f"**🍽️ Restaurants:** {amenities['restaurants']}+")
                        
                        if 'gyms' in amenities:
                            st.write(f"**💪 Gyms:** {amenities['gyms']}")
                        
                        if 'banks' in amenities:
                            st.write(f"**🏦 Banks:** {amenities['banks']}")
                        
                        if 'cinemas' in amenities:
                            st.write(f"**🎬 Cinemas:** {amenities['cinemas']}")
                else:
                    st.info("Amenity details not available for this location.")
            
            with tab4:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**✈️ Airport Access**")
                    airport = location_info.get('nearest_airport', {})
                    if airport:
                        st.write(f"• {airport.get('name', 'Airport')}")
                        st.write(f"• Distance: {airport.get('distance_km', 'N/A')} km")
                    
                    st.write("**🚂 Railway Connectivity**")
                    railway = location_info.get('nearest_railway', {})
                    if railway:
                        st.write(f"• {railway.get('name', 'Railway Station')}")
                        st.write(f"• Distance: {railway.get('distance_km', 'N/A')} km")
                
                with col2:
                    st.write("**🚇 Metro Access**")
                    metro = location_info.get('metro', {})
                    if metro and metro.get('available'):
                        st.write(f"• Station: {metro.get('station', 'N/A')}")
                        st.write(f"• Distance: {metro.get('distance_km', 'N/A')} km")
                        st.success("✅ Metro connectivity available")
                    else:
                        st.warning("❌ No metro connectivity")
                    
                    st.write("**🚌 Public Transport**")
                    transport = location_info.get('public_transport', {})
                    if transport:
                        st.write(f"• Bus routes: {transport.get('bus_routes', 'N/A')}")
                        st.write(f"• Auto availability: {transport.get('auto_availability', 'N/A')}")
                        st.write(f"• Cab services: {transport.get('uber_ola', 'N/A')}")
            
            # Add to comparison
            if st.button(f"➕ Add {selected_location} to Comparison", key="add_to_comparison"):
                if selected_location not in st.session_state.selected_locations:
                    st.session_state.selected_locations.append(selected_location)
                    st.success(f"✅ Added {selected_location} to comparison list!")
                else:
                    st.warning("⚠️ This location is already in your comparison list.")
        
        else:
            st.error(f"❌ {location_info['error']}")

elif page == "💰 Investment Analysis":
    st.header("💰 Investment Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        locations = df['location'].tolist()
        selected_location = st.selectbox(
            "🏘️ Select location for investment analysis:",
            options=locations
        )
    
    with col2:
        investment_amount = st.number_input(
            "💵 Investment Amount (₹)",
            min_value=1000000,
            max_value=1000000000,
            value=20000000,
            step=1000000,
            format="%d"
        )
    
    if st.button("📊 Analyze Investment Potential", type="primary"):
        with st.spinner("🔄 Calculating investment metrics..."):
            investment_result = get_investment_analysis(selected_location, investment_amount)
            
            if 'error' not in investment_result:
                analysis = investment_result['analysis']
                
                # Key metrics
                st.subheader("📈 Investment Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    roi = analysis['roi_percentage']
                    st.metric(
                        "🎯 Expected ROI",
                        f"{roi:.1f}%",
                        delta="Annually"
                    )
                
                with col2:
                    monthly_rent = analysis['monthly_rental_income']
                    st.metric(
                        "🏠 Monthly Rental",
                        f"₹{monthly_rent:,.0f}",
                        delta="Income"
                    )
                
                with col3:
                    appreciation = analysis['yearly_appreciation']
                    st.metric(
                        "📈 Annual Appreciation",
                        f"₹{appreciation:,.0f}",
                        delta="Value Growth"
                    )
                
                with col4:
                    payback = analysis['payback_period_years']
                    st.metric(
                        "⏱️ Payback Period",
                        f"{payback} years",
                        delta="ROI Timeline"
                    )
                
                # Risk assessment
                risk_level = analysis['risk_level']
                recommendation = analysis['recommendation']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if risk_level == "Low Risk":
                        st.success(f"✅ **Risk Level**: {risk_level}")
                    elif risk_level == "Medium Risk":
                        st.warning(f"⚠️ **Risk Level**: {risk_level}")
                    else:
                        st.error(f"❌ **Risk Level**: {risk_level}")
                
                with col2:
                    if recommendation == "Highly Recommended":
                        st.success(f"🌟 **Recommendation**: {recommendation}")
                    elif recommendation == "Recommended":
                        st.success(f"👍 **Recommendation**: {recommendation}")
                    elif recommendation == "Consider with Caution":
                        st.warning(f"⚠️ **Recommendation**: {recommendation}")
                    else:
                        st.error(f"❌ **Recommendation**: {recommendation}")
                
                # Risk factors
                if analysis['risk_factors']:
                    st.subheader("⚠️ Risk Factors")
                    for risk in analysis['risk_factors']:
                        st.write(f"• {risk}")
                
                # Market trends
                if 'market_trends' in investment_result:
                    st.subheader("📊 Market Analysis")
                    trends = investment_result['market_trends']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📈 Market Outlook**: {trends.get('market_outlook', 'N/A')}")
                        st.write(f"**💹 Growth Forecast**: {trends.get('price_growth_forecast', 'N/A')}")
                    
                    with col2:
                        st.write("**🎯 Key Growth Drivers**:")
                        for driver in trends.get('key_drivers', []):
                            st.write(f"• {driver}")
                
                # Comparable investments
                if 'comparable_locations' in investment_result:
                    st.subheader("🔄 Similar Investment Options")
                    comparables_df = pd.DataFrame(investment_result['comparable_locations'])
                    
                    if not comparables_df.empty:
                        st.dataframe(
                            comparables_df,
                            use_container_width=True,
                            hide_index=True
                        )
                
                # Investment breakdown chart
                st.subheader("💰 Investment Breakdown")
                
                breakdown_data = {
                    'Component': ['Area Purchased', 'Monthly Rental Income', 'Annual Appreciation'],
                    'Value': [
                        analysis['area_purchased_sqft'],
                        analysis['monthly_rental_income'] * 12,
                        analysis['yearly_appreciation']
                    ],
                    'Unit': ['sq ft', '₹ (Annual)', '₹']
                }
                
                fig_breakdown = px.bar(
                    x=breakdown_data['Component'],
                    y=[breakdown_data['Value'][0] / 100, breakdown_data['Value'][1], breakdown_data['Value'][2]],
                    title="Investment Component Analysis",
                    labels={'x': 'Components', 'y': 'Value (normalized)'}
                )
                
                st.plotly_chart(fig_breakdown, use_container_width=True)
            
            else:
                st.error(f"❌ {investment_result['error']}")

elif page == "⚖️ Location Comparison":
    st.header("⚖️ Location Comparison")
    
    # Current comparison list
    if st.session_state.selected_locations:
        st.subheader("📋 Current Comparison List")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            for i, location in enumerate(st.session_state.selected_locations):
                st.write(f"• {location}")
        
        with col2:
            if st.button("🗑️ Clear List"):
                st.session_state.selected_locations = []
                st.rerun()
    
    # Add more locations
    st.subheader("➕ Add Locations to Compare")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        available_locations = [loc for loc in df['location'].tolist() 
                              if loc not in st.session_state.selected_locations]
        
        if available_locations:
            new_location = st.selectbox(
                "Select location to add:",
                options=available_locations,
                key="new_location_select"
            )
            
            if st.button("➕ Add to Comparison"):
                if new_location:
                    st.session_state.selected_locations.append(new_location)
                    st.rerun()
        else:
            st.info("All locations are already added to comparison.")
    
    with col2:
        st.info(f"**Selected**: {len(st.session_state.selected_locations)} locations")
    
    # Perform comparison
    if len(st.session_state.selected_locations) >= 2:
        if st.button("🔍 Compare Locations", type="primary"):
            with st.spinner("🔄 Analyzing locations..."):
                comparison_result = compare_locations(st.session_state.selected_locations)
                
                if 'error' not in comparison_result:
                    st.session_state.comparison_data = comparison_result
                else:
                    st.error(f"❌ {comparison_result['error']}")
    
    # Display comparison results
    if st.session_state.comparison_data:
        comparison = st.session_state.comparison_data
        
        st.subheader("🏆 Comparison Results")
        
        # Winners summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🛡️ Safest Location",
                comparison['winners']['safety_score']
            )
        
        with col2:
            st.metric(
                "💰 Best Investment",
                comparison['winners']['appreciation_rate']
            )
        
        with col3:
            st.metric(
                "🏆 Overall Winner",
                comparison['overall_winner']
            )
        
        # Detailed comparison table
        st.subheader("📊 Detailed Comparison")
        
        metrics_df_data = []
        for location in comparison['locations']:
            location_data = get_neighborhood_info(location)
            if 'error' not in location_data:
                metrics_df_data.append({
                    'Location': location,
                    'Safety Score': location_data.get('safety_score', 0),
                    'Price/sq ft': f"₹{location_data.get('avg_price_per_sqft', 0):,}",
                    'Investment Score': location_data.get('investment_score', 0),
                    'Schools': location_data.get('schools', 0),
                    'Connectivity': location_data.get('connectivity_score', 0),
                    'Future Growth': location_data.get('future_growth', 'N/A')
                })
        
        if metrics_df_data:
            comparison_df = pd.DataFrame(metrics_df_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Summary recommendations
        if 'summary' in comparison:
            st.subheader("💡 Recommendations")
            summary = comparison['summary']
            
            for location, recommendations in summary.get('recommendations', {}).items():
                if recommendations:
                    st.write(f"**{location}:**")
                    for rec in recommendations:
                        st.write(f"• {rec}")
    
    elif len(st.session_state.selected_locations) < 2:
        st.info("👆 Please add at least 2 locations to start comparison.")

elif page == "📊 Market Insights":
    st.header("📊 Market Insights & Analytics")
    
    # Market overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏙️ City-wise Distribution")
        city_counts = df['city'].value_counts()
        fig_pie = px.pie(
            values=city_counts.values,
            names=city_counts.index,
            title="Locations by City"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📈 Growth Potential")
        growth_counts = df['future_growth'].value_counts()
        fig_bar = px.bar(
            x=growth_counts.index,
            y=growth_counts.values,
            title="Areas by Growth Potential",
            color=growth_counts.values,
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Price analysis
    st.subheader("💰 Price Analysis")
    
    # Price trends
    fig_price_trend = px.histogram(
        df,
        x='avg_price_per_sqft',
        nbins=20,
        title="Price Distribution",
        labels={'avg_price_per_sqft': 'Price per Sq Ft (₹)', 'count': 'Number of Areas'}
    )
    st.plotly_chart(fig_price_trend, use_container_width=True)
    
    # Correlation analysis
    st.subheader("🔗 Factor Correlations")
    
    numeric_cols = ['safety_score', 'traffic_score', 'schools', 'hospitals', 
                   'avg_price_per_sqft', 'rental_yield', 'appreciation_rate',
                   'connectivity_score', 'infrastructure_score', 'lifestyle_score']
    
    correlation_matrix = df[numeric_cols].corr()
    
    fig_heatmap = px.imshow(
        correlation_matrix,
        text_auto=True,
        aspect="auto",
        title="Correlation Matrix: Key Factors",
        color_continuous_scale="RdBu"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Top performers
    st.subheader("🏆 Top Performers")
    
    tab1, tab2, tab3 = st.tabs(["🛡️ Safety", "💰 Investment", "🏫 Education"])
    
    with tab1:
        top_safety = df.nlargest(5, 'safety_score')[['location', 'safety_score', 'city']]
        st.dataframe(top_safety, hide_index=True, use_container_width=True)
    
    with tab2:
        top_investment = df.nlargest(5, 'investment_score')[['location', 'investment_score', 'appreciation_rate', 'rental_yield']]
        st.dataframe(top_investment, hide_index=True, use_container_width=True)
    
    with tab3:
        top_education = df.nlargest(5, 'schools')[['location', 'schools', 'hospitals', 'safety_score']]
        st.dataframe(top_education, hide_index=True, use_container_width=True)

elif page == "🤖 AI Analysis":
    st.header("🤖 AI-Powered Analysis")
    
    # AI analysis options
    analysis_type = st.selectbox(
        "🎯 Choose analysis type:",
        [
            "Detailed Location Analysis",
            "Investment Focus",
            "Family-Oriented Analysis",
            "Market Insights",
            "Investment Strategy",
            "Location Comparison"
        ]
    )
    
    if analysis_type in ["Detailed Location Analysis", "Investment Focus", "Family-Oriented Analysis"]:
        locations = df['location'].tolist()
        selected_location = st.selectbox(
            "🏘️ Select location:",
            options=locations
        )
        
        if st.button("🚀 Generate AI Analysis", type="primary"):
            with st.spinner("🤖 AI is analyzing the location..."):
                location_info = get_neighborhood_info(selected_location)
                
                if 'error' not in location_info:
                    analysis_type_map = {
                        "Detailed Location Analysis": "detailed_analysis",
                        "Investment Focus": "investment_focus", 
                        "Family-Oriented Analysis": "family_focus"
                    }
                    
                    ai_result = get_deepseek_scorecard(
                        location_info, 
                        analysis_type_map[analysis_type]
                    )
                    
                    st.subheader(f"🤖 AI Analysis: {selected_location}")
                    st.write(ai_result['analysis'])
                    
                    # Analysis metadata
                    with st.expander("📊 Analysis Details"):
                        st.write(f"**Analysis Type**: {ai_result['analysis_type']}")
                        st.write(f"**Generated At**: {ai_result['generated_at']}")
                        st.write(f"**API Calls Made**: {ai_result['api_calls_made']}")
                
                else:
                    st.error(f"❌ {location_info['error']}")
    
    elif analysis_type == "Market Insights":
        city_filter = st.selectbox(
            "🏙️ Select city (optional):",
            options=["All Cities", "Ahmedabad", "Gandhinagar"],
            index=0
        )
        
        if st.button("🚀 Generate Market Analysis", type="primary"):
            with st.spinner("🤖 AI is analyzing market trends..."):
                city = None if city_filter == "All Cities" else city_filter
                market_analysis = get_market_insights(city)
                
                st.subheader(f"🤖 Market Analysis: {city_filter}")
                st.write(market_analysis)
    
    elif analysis_type == "Investment Strategy":
        col1, col2 = st.columns(2)
        
        with col1:
            budget = st.number_input(
                "💰 Investment Budget (₹)",
                min_value=1000000,
                max_value=500000000,
                value=25000000,
                step=1000000
            )
        
        with col2:
            goals = st.selectbox(
                "🎯 Investment Goals:",
                [
                    "balanced growth",
                    "high appreciation",
                    "steady rental income",
                    "low risk conservative",
                    "aggressive growth"
                ]
            )
        
        if st.button("🚀 Generate Investment Strategy", type="primary"):
            with st.spinner("🤖 AI is creating your investment strategy..."):
                strategy = get_investment_strategy(budget, goals)
                
                st.subheader(f"🤖 Personalized Investment Strategy")
                st.write(strategy)
    
    elif analysis_type == "Location Comparison":
        if len(st.session_state.selected_locations) >= 2:
            if st.button("🚀 Generate AI Comparison", type="primary"):
                with st.spinner("🤖 AI is comparing locations..."):
                    locations_data = []
                    for location in st.session_state.selected_locations:
                        loc_info = get_neighborhood_info(location)
                        if 'error' not in loc_info:
                            locations_data.append(loc_info)
                    
                    if len(locations_data) >= 2:
                        comparison_analysis = get_comparative_analysis(locations_data)
                        
                        st.subheader("🤖 AI Comparative Analysis")
                        st.write(comparison_analysis)
                    else:
                        st.error("❌ Could not retrieve data for comparison locations.")
        else:
            st.info("👆 Please add at least 2 locations to your comparison list first (use Location Explorer).")
    
    # AI Statistics
    with st.expander("📊 AI Usage Statistics"):
        stats = get_api_stats()
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🔢 Total API Calls", stats['total_api_calls'])
        
        with col2:
            st.write(f"**🔑 API Configured**: {'✅ Yes' if stats['api_key_configured'] else '❌ No'}")
        
        if stats['last_api_call']:
            st.write(f"**⏰ Last Call**: {stats['last_api_call']}")

elif page == "📈 Top Picks":
    st.header("📈 Top Location Picks")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criteria = st.selectbox(
            "🎯 Ranking Criteria:",
            ['overall', 'investment', 'safety', 'affordability', 'lifestyle', 'connectivity']
        )
    
    with col2:
        budget_max = st.number_input(
            "💰 Max Budget (₹/sq ft)",
            min_value=0,
            max_value=20000,
            value=0,
            step=500
        )
    
    with col3:
        city_filter = st.selectbox(
            "🏙️ City Filter:",
            ['All', 'Ahmedabad', 'Gandhinagar']
        )
    
    with col4:
        limit = st.slider("📊 Number of Results", 3, 10, 5)
    
    # Get recommendations
    budget_filter = None if budget_max == 0 else budget_max
    city = None if city_filter == 'All' else city_filter
    
    recommendations = get_top_locations(criteria, budget_filter, city, limit)
    
    if 'error' not in recommendations:
        st.subheader(f"🏆 Top {limit} Locations for {criteria.title()}")
        
        for i, location in enumerate(recommendations['locations'], 1):
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.markdown(f"### #{i}")
                
                with col2:
                    st.write(f"**📍 {location['location']}**")
                    st.write(f"🏙️ {location['city']}")
                    st.write(f"⭐ Score: {location['score']}")
                    st.write(f"💰 ₹{location['price_per_sqft']:,}/sq ft")
                    
                    # Key highlights
                    if location['key_highlights']:
                        st.write("**✨ Highlights:**")
                        for highlight in location['key_highlights']:
                            st.write(f"• {highlight}")
                
                with col3:
                    if st.button(f"👀 View Details", key=f"view_{i}"):
                        st.info(f"Use Location Explorer to see detailed information about {location['location']}")
                
                st.divider()
        
        st.info(f"📊 Found {recommendations['total_found']} locations matching criteria, showing top {recommendations['showing_top']}")
    
    else:
        st.error(f"❌ {recommendations['error']}")

elif page == "📋 Export Reports":
    st.header("📋 Export Analysis Reports")
    
    locations = df['location'].tolist()
    selected_location = st.selectbox(
        "🏘️ Select location for report:",
        options=locations
    )
    
    report_name = st.text_input(
        "📝 Report Name (optional):",
        value="",
        placeholder="e.g., Investment_Analysis_2024"
    )
    
    if st.button("📄 Generate Comprehensive Report", type="primary"):
        with st.spinner("📊 Generating comprehensive analysis report..."):
            filename = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json" if report_name else None
            
            export_result = export_analysis_report(selected_location, filename)
            
            if 'error' not in export_result:
                st.success(f"✅ {export_result['success']}")
                
                # Offer download
                try:
                    with open(export_result['filename'], 'r') as f:
                        report_content = f.read()
                    
                    st.download_button(
                        label="⬇️ Download Report",
                        data=report_content,
                        file_name=export_result['filename'],
                        mime="application/json"
                    )
                except:
                    st.warning("⚠️ Report generated but download not available.")
            
            else:
                st.error(f"❌ {export_result['error']}")
    
    st.info("💡 **Report includes**: Location overview, investment analysis, market position, and detailed recommendations")

elif page == "⚙️ Settings":
    st.header("⚙️ Settings & Configuration")
    
    # Data information
    st.subheader("📊 Data Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📍 Total Locations", len(df))
        st.metric("🏙️ Cities Covered", df['city'].nunique())
        st.metric("📅 Data Points per Location", len(df.columns))
    
    with col2:
        st.write("**🏙️ Cities:**")
        for city in df['city'].unique():
            count = len(df[df['city'] == city])
            st.write(f"• {city}: {count} locations")
    
    # Clear cache
    st.subheader("🧹 Cache Management")
    
    if st.button("🗑️ Clear All Cache"):
        st.cache_data.clear()
        if 'selected_locations' in st.session_state:
            st.session_state.selected_locations = []
        if 'comparison_data' in st.session_state:
            st.session_state.comparison_data = None
        st.success("✅ Cache cleared successfully!")
    
    # API status
    st.subheader("🤖 AI Service Status")
    stats = get_api_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if stats['api_key_configured']:
            st.success("✅ DeepSeek API: Configured")
        else:
            st.error("❌ DeepSeek API: Not Configured")
    
    with col2:
        st.write(f"**Model**: {stats['model_name']}")
        st.write(f"**Total Calls**: {stats['total_api_calls']}")
    
    # About
    st.subheader("ℹ️ About")
    st.write("""
    **🏘️ Smart Neighborhood Analysis Tool v2.0**
    
    A comprehensive real estate analysis platform for Ahmedabad and Gandhinagar featuring:
    - 🔍 Detailed location insights
    - 💰 Investment analysis with ROI calculations
    - ⚖️ Multi-location comparison
    - 🤖 AI-powered market analysis
    - 📊 Interactive visualizations
    - 📋 Comprehensive reporting
    
    Built with ❤️ using Streamlit, Plotly, and advanced AI integration.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🏘️ Smart Neighborhood Analysis Tool | Built with Streamlit & AI | © 2024"
    "</div>", 
    unsafe_allow_html=True
)

# Run the app
if __name__ == '__main__':
    st.write("🚀 App loaded successfully!")