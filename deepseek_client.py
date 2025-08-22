"""
Enhanced DeepSeek AI Client for Neighborhood Analysis
Provides sophisticated AI-powered analysis with multiple analysis types and advanced prompting
"""

import logging
import json
import re
import os
from dotenv import load_dotenv
import requests
from typing import Dict, List, Optional
from datetime import datetime
import time

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"

# API call tracking
api_calls_count = 0
last_api_call = 0
MIN_API_INTERVAL = 1  # Minimum 1 second between API calls

# Enhanced prompt templates for different analysis types
PROMPT_TEMPLATES = {
    'detailed_analysis': '''
As a real estate expert and urban planner, provide a comprehensive analysis of {location}.

Location Data:
{location_data}

Please provide:
1. **Location Overview**: Brief description and key characteristics
2. **Strengths Analysis**: Top 3-5 advantages of this location
3. **Areas for Improvement**: 2-3 aspects that could be better
4. **Investment Perspective**: 
   - Short-term outlook (1-2 years)
   - Long-term potential (5-10 years)
   - Risk assessment
5. **Target Demographics**: Who would benefit most from living here?
6. **Comparison Context**: How does this compare to similar areas?
7. **Actionable Recommendations**: Specific advice for potential buyers/investors

Provide practical, data-driven insights in a professional yet accessible tone.
''',
    
    'investment_focus': '''
As an investment advisor specializing in real estate, analyze {location} for investment potential.

Investment Metrics:
{investment_data}

Focus on:
1. **ROI Analysis**: Expected returns and timeline
2. **Risk Assessment**: Market risks and mitigation strategies
3. **Growth Drivers**: Factors that will drive property value appreciation
4. **Market Positioning**: How this investment compares to alternatives
5. **Entry Strategy**: Best approach for different investment sizes
6. **Exit Strategy**: When and how to realize gains

Provide specific, actionable investment advice.
''',
    
    'family_focus': '''
As a family relocation specialist, evaluate {location} for families with children.

Family-Relevant Data:
{family_data}

Address:
1. **Education Quality**: Schools and educational opportunities
2. **Safety & Security**: Crime rates, neighborhood safety measures
3. **Community & Lifestyle**: Family-friendly amenities and activities
4. **Healthcare Access**: Medical facilities and emergency services
5. **Transportation**: Commute options and accessibility
6. **Cost of Living**: Budget considerations for families
7. **Long-term Suitability**: Growing with your family's needs

Provide family-centric recommendations and practical advice.
'''
}

def build_prompt(location_info: Dict, analysis_type: str = 'detailed_analysis', custom_focus: Optional[str] = None) -> str:
    """
    Build sophisticated prompts for DeepSeek API based on analysis type.
    
    Args:
        location_info (dict): Dictionary with neighborhood data
        analysis_type (str): Type of analysis ('detailed_analysis', 'investment_focus', 'family_focus')
        custom_focus (str, optional): Custom analysis focus
    
    Returns:
        str: Formatted prompt string for API consumption
    """
    # Extract location name
    location_name = location_info.get('location', location_info.get('name', 'Unknown Location'))
    
    # Build comprehensive location data string
    location_data_parts = []
    
    # Basic information
    if 'city' in location_info:
        location_data_parts.append(f"City: {location_info['city']}")
    if 'area' in location_info:
        location_data_parts.append(f"Area: {location_info['area']}")
    if 'population' in location_info and location_info['population']:
        location_data_parts.append(f"Population: {location_info['population']:,}")
    if 'population_density' in location_info and location_info['population_density']:
        location_data_parts.append(f"Population Density: {location_info['population_density']:,} per sq km")
    
    # Scores and ratings
    location_data_parts.append(f"Safety Score: {location_info.get('safety_score', 'N/A')}/10")
    location_data_parts.append(f"Traffic Score: {location_info.get('traffic_score', 'N/A')}/10 (lower is better)")
    location_data_parts.append(f"Infrastructure Score: {location_info.get('infrastructure_score', 'N/A')}/10")
    location_data_parts.append(f"Connectivity Score: {location_info.get('connectivity_score', 'N/A')}/10")
    location_data_parts.append(f"Lifestyle Score: {location_info.get('lifestyle_score', 'N/A')}/10")
    location_data_parts.append(f"Environment Score: {location_info.get('environment_score', 'N/A')}/10")
    
    # Infrastructure and amenities
    location_data_parts.append(f"Schools: {location_info.get('schools', 'N/A')}")
    location_data_parts.append(f"Hospitals: {location_info.get('hospitals', 'N/A')}")
    
    # Transportation
    if 'metro' in location_info and isinstance(location_info['metro'], dict):
        metro = location_info['metro']
        if metro.get('available'):
            location_data_parts.append(f"Metro: Yes, {metro.get('station', 'N/A')} station ({metro.get('distance_km', 'N/A')} km away)")
        else:
            location_data_parts.append("Metro: Not available")
    
    # Economic data
    location_data_parts.append(f"Average Price per Sq Ft: ₹{location_info.get('avg_price_per_sqft', 'N/A'):,}")
    if 'rental_yield' in location_info:
        location_data_parts.append(f"Rental Yield: {location_info['rental_yield']}%")
    if 'appreciation_rate' in location_info:
        location_data_parts.append(f"Historical Appreciation Rate: {location_info['appreciation_rate']}%")
    location_data_parts.append(f"Future Growth Potential: {location_info.get('future_growth', 'N/A')}")
    
    # Calculated metrics if available
    if 'calculated_metrics' in location_info:
        metrics = location_info['calculated_metrics']
        if 'overall_rating' in metrics:
            location_data_parts.append(f"Overall Rating: {metrics['overall_rating']}/10")
        if 'affordability_index' in metrics:
            location_data_parts.append(f"Affordability Index: {metrics['affordability_index']}/10")
    
    # Amenities
    if 'amenities' in location_info and isinstance(location_info['amenities'], dict):
        amenities = location_info['amenities']
        if 'malls' in amenities and amenities['malls']:
            location_data_parts.append(f"Major Malls: {', '.join(amenities['malls'][:3])}")
        if 'restaurants' in amenities:
            location_data_parts.append(f"Restaurants: {amenities['restaurants']}+")
        if 'parks' in amenities and amenities['parks']:
            location_data_parts.append(f"Parks/Recreation: {', '.join(amenities['parks'][:2])}")
    
    location_data_str = '\n'.join(f"• {part}" for part in location_data_parts)
    
    # Select appropriate template
    if custom_focus:
        template = f"As a real estate expert, analyze {location_name} with focus on: {custom_focus}\n\nLocation Data:\n{location_data_str}\n\nPlease provide comprehensive insights addressing the specified focus area."
    else:
        template = PROMPT_TEMPLATES.get(analysis_type, PROMPT_TEMPLATES['detailed_analysis'])
        
        # Prepare template-specific data
        if analysis_type == 'investment_focus':
            investment_data = f"""
• Investment Score: {location_info.get('investment_score', 'N/A')}/10
• Current Price: ₹{location_info.get('avg_price_per_sqft', 'N/A'):,}/sq ft
• Rental Yield: {location_info.get('rental_yield', 'N/A')}%
• Appreciation Rate: {location_info.get('appreciation_rate', 'N/A')}%
• Growth Potential: {location_info.get('future_growth', 'N/A')}
• Connectivity Score: {location_info.get('connectivity_score', 'N/A')}/10
{location_data_str}"""
            template = template.format(location=location_name, investment_data=investment_data)
        
        elif analysis_type == 'family_focus':
            family_data = f"""
• Safety Score: {location_info.get('safety_score', 'N/A')}/10
• Number of Schools: {location_info.get('schools', 'N/A')}
• Number of Hospitals: {location_info.get('hospitals', 'N/A')}
• Traffic Conditions: {location_info.get('traffic_score', 'N/A')}/10 (lower is better)
• Environment Quality: {location_info.get('environment_score', 'N/A')}/10
• Lifestyle Amenities: {location_info.get('lifestyle_score', 'N/A')}/10
{location_data_str}"""
            template = template.format(location=location_name, family_data=family_data)
        
        else:
            template = template.format(location=location_name, location_data=location_data_str)
    
    return template

def call_deepseek(prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    Enhanced DeepSeek API call with rate limiting and error handling.
    
    Args:
        prompt (str): The prompt to send to DeepSeek
        temperature (float): Response creativity (0.0-1.0)
        max_tokens (int): Maximum response length
    
    Returns:
        str: AI-generated response or error message
    """
    global api_calls_count, last_api_call
    
    if not DEEPSEEK_API_KEY:
        logging.error("DeepSeek API key not found in environment variables")
        return "Error: DeepSeek API key is not configured. Please set DEEPSEEK_API_KEY in your environment variables."
    
    # Rate limiting
    current_time = time.time()
    if current_time - last_api_call < MIN_API_INTERVAL:
        time.sleep(MIN_API_INTERVAL - (current_time - last_api_call))
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert real estate analyst and urban planning consultant with extensive knowledge of Indian real estate markets, particularly Gujarat. Provide detailed, accurate, and actionable insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    try:
        logging.info(f"Making DeepSeek API call #{api_calls_count + 1}")
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result_json = response.json()
        api_calls_count += 1
        last_api_call = time.time()
        
        if 'choices' in result_json and len(result_json['choices']) > 0:
            content = result_json['choices'][0]['message']['content']
            
            # Log usage statistics
            if 'usage' in result_json:
                usage = result_json['usage']
                logging.info(f"DeepSeek API usage - Prompt tokens: {usage.get('prompt_tokens', 'N/A')}, "
                           f"Completion tokens: {usage.get('completion_tokens', 'N/A')}, "
                           f"Total tokens: {usage.get('total_tokens', 'N/A')}")
            
            return content.strip()
        else:
            logging.error("Unexpected response structure from DeepSeek API")
            return "Error: Received unexpected response format from AI service. Please try again."
    
    except requests.exceptions.Timeout:
        logging.error("DeepSeek API request timed out")
        return "Error: AI service request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API request failed: {str(e)}")
        return f"Error: AI service request failed - {str(e)}. Please check your internet connection and try again."
    except Exception as e:
        logging.error(f"Unexpected error in DeepSeek API call: {str(e)}")
        return "Error: An unexpected error occurred while processing your request. Please try again."

def get_deepseek_scorecard(location_info: Dict, analysis_type: str = 'detailed_analysis') -> Dict:
    """
    Get comprehensive AI analysis for a location.
    
    Args:
        location_info (dict): Dictionary with neighborhood data
        analysis_type (str): Type of analysis to perform
    
    Returns:
        dict: API response with generated analysis or error
    """
    prompt = build_prompt(location_info, analysis_type)
    result = call_deepseek(prompt)
    
    return {
        'location': location_info.get('location', location_info.get('name', 'Unknown')),
        'analysis_type': analysis_type,
        'generated_at': datetime.now().isoformat(),
        'analysis': result,
        'api_calls_made': api_calls_count
    }

def get_comparative_analysis(location_data_list: List[Dict]) -> str:
    """
    Generate comparative analysis for multiple locations.
    
    Args:
        location_data_list (List[Dict]): List of location data dictionaries
    
    Returns:
        str: Comparative analysis
    """
    if len(location_data_list) < 2:
        return "Error: At least 2 locations required for comparison."
    
    locations_summary = []
    for loc in location_data_list:
        summary = f"""
**{loc.get('location', 'Unknown Location')}:**
• Safety: {loc.get('safety_score', 'N/A')}/10
• Price: ₹{loc.get('avg_price_per_sqft', 'N/A'):,}/sq ft
• Investment Score: {loc.get('investment_score', 'N/A')}/10
• Growth Potential: {loc.get('future_growth', 'N/A')}
• Schools: {loc.get('schools', 'N/A')}
• Connectivity: {loc.get('connectivity_score', 'N/A')}/10"""
        locations_summary.append(summary)
    
    prompt = f"""
As a real estate expert, provide a comprehensive comparison of these {len(location_data_list)} locations:

{chr(10).join(locations_summary)}

Please provide:
1. **Comparative Overview**: Key differences and similarities
2. **Best For Investment**: Which location offers the best investment potential and why
3. **Best For Families**: Which location is most suitable for families with children
4. **Best Value for Money**: Which offers the best balance of features vs. cost
5. **Future Outlook**: Which has the strongest growth prospects
6. **Specific Recommendations**: Who should consider each location and why

Provide detailed reasoning for each recommendation.
"""
    
    return call_deepseek(prompt, temperature=0.6)

def get_market_insights(city: str = None) -> str:
    """
    Generate market insights and trends analysis.
    
    Args:
        city (str, optional): Specific city to analyze
    
    Returns:
        str: Market insights analysis
    """
    market_context = "Ahmedabad and Gandhinagar real estate markets" if not city else f"{city} real estate market"
    
    prompt = f"""
As a real estate market analyst, provide current insights about the {market_context}:

1. **Market Trends**: Current state of the property market
2. **Price Movements**: Recent price trends and predictions
3. **Investment Hotspots**: Areas showing strong growth potential
4. **Buyer Preferences**: What buyers are currently looking for
5. **Infrastructure Impact**: How infrastructure development affects property values
6. **Risk Factors**: Potential challenges and how to mitigate them
7. **Future Outlook**: 2-3 year market predictions

Base your analysis on typical Gujarat real estate patterns and provide actionable insights.
"""
    
    return call_deepseek(prompt, temperature=0.5)

def get_investment_strategy(budget: float, investment_goals: str = "balanced growth") -> str:
    """
    Get personalized investment strategy recommendations.
    
    Args:
        budget (float): Investment budget in INR
        investment_goals (str): Investment objectives
    
    Returns:
        str: Investment strategy recommendations
    """
    budget_category = "High" if budget > 50000000 else "Medium" if budget > 20000000 else "Entry Level"
    
    prompt = f"""
As an investment advisor, create a personalized real estate investment strategy:

**Investment Profile:**
• Budget: ₹{budget:,.0f} ({budget_category} investor)
• Goals: {investment_goals}
• Market Focus: Ahmedabad and Gandhinagar

Provide:
1. **Strategy Overview**: Recommended approach for this budget and goals
2. **Area Recommendations**: Which neighborhoods to focus on and why
3. **Property Type Suggestions**: Residential vs commercial considerations
4. **Timeline**: Short-term vs long-term investment approach
5. **Risk Management**: How to minimize investment risks
6. **Portfolio Diversification**: If applicable, how to spread investments
7. **Exit Strategy**: When and how to realize returns
8. **Action Plan**: Specific next steps to take

Provide practical, actionable advice tailored to the Indian real estate market.
"""
    
    return call_deepseek(prompt, temperature=0.6)

# API statistics
def get_api_stats() -> Dict:
    """
    Get API usage statistics.
    
    Returns:
        dict: API usage statistics
    """
    return {
        'total_api_calls': api_calls_count,
        'last_api_call': datetime.fromtimestamp(last_api_call).isoformat() if last_api_call else None,
        'api_key_configured': bool(DEEPSEEK_API_KEY),
        'model_name': MODEL_NAME
    }

# Legacy support functions (maintained for backward compatibility)
def sanitize_input(text: str) -> str:
    """
    Sanitize input by removing extra whitespace and special characters.
    Convert to lowercase for consistency.
    
    Args:
        text (str): Input string to sanitize
    
    Returns:
        str: Sanitized and lowercase string
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return ' '.join(text.strip().split()).lower()

# Example usage and testing
if __name__ == '__main__':
    print("=== DeepSeek AI Client Test ===")
    
    # Test with sample location data
    sample_location = {
        'location': 'Satellite, Ahmedabad',
        'city': 'Ahmedabad',
        'area': 'Satellite',
        'safety_score': 8.2,
        'traffic_score': 6.8,
        'schools': 15,
        'hospitals': 8,
        'future_growth': 'High',
        'avg_price_per_sqft': 6500,
        'rental_yield': 3.2,
        'appreciation_rate': 8.5,
        'connectivity_score': 9.1,
        'infrastructure_score': 8.7
    }
    
    print("\n1. Testing detailed analysis:")
    result = get_deepseek_scorecard(sample_location, 'detailed_analysis')
    print(f"Analysis type: {result['analysis_type']}")
    print(f"Generated at: {result['generated_at']}")
    print(f"API calls made: {result['api_calls_made']}")
    
    if not result['analysis'].startswith('Error:'):
        print("✅ Analysis generated successfully")
    else:
        print(f"❌ Error: {result['analysis']}")
    
    print("\n2. API Statistics:")
    stats = get_api_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")