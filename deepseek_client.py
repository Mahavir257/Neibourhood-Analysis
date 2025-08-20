import logging
import json
import re
import os
from dotenv import load_dotenv
import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"

# Centralized neighborhood data
NEIGHBORHOODS = {
    'ahmedabad': [
        {'name': 'Navrangpura', 'population': 50000, 'area_sqkm': 5.2, 'safety_score': 8.5, 'traffic_score': 6.0, 'schools': 'Good', 'hospitals': 'Excellent', 'future_growth': 'High', 'avg_price_per_sqft': 7500},
        {'name': 'Vastrapur', 'population': 45000, 'area_sqkm': 4.8, 'safety_score': 7.8, 'traffic_score': 5.5, 'schools': 'Excellent', 'hospitals': 'Good', 'future_growth': 'Moderate', 'avg_price_per_sqft': 7000},
        {'name': 'Maninagar', 'population': 60000, 'area_sqkm': 6.0, 'safety_score': 7.0, 'traffic_score': 4.5, 'schools': 'Average', 'hospitals': 'Good', 'future_growth': 'Low', 'avg_price_per_sqft': 6500}
    ],
    'gandhinagar': [
        {'name': 'Sector 21', 'population': 20000, 'area_sqkm': 3.5, 'safety_score': 9.0, 'traffic_score': 8.0, 'schools': 'Excellent', 'hospitals': 'Excellent', 'future_growth': 'High', 'avg_price_per_sqft': 6000},
        {'name': 'Sector 7', 'population': 18000, 'area_sqkm': 3.0, 'safety_score': 8.8, 'traffic_score': 7.5, 'schools': 'Good', 'hospitals': 'Good', 'future_growth': 'Moderate', 'avg_price_per_sqft': 5800},
        {'name': 'Kudasan', 'population': 25000, 'area_sqkm': 4.0, 'safety_score': 8.2, 'traffic_score': 6.5, 'schools': 'Good', 'hospitals': 'Average', 'future_growth': 'High', 'avg_price_per_sqft': 6200}
    ]
}

def sanitize_input(text):
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

def get_neighborhood_info(city, neighborhood):
    """
    Retrieve neighborhood information for Ahmedabad or Gandhinagar with case-insensitive matching.
    
    Args:
        city (str): Name of the city (e.g., 'Ahmedabad', 'Gandhinagar')
        neighborhood (str): Name of the neighborhood
    
    Returns:
        dict: Detailed information about the neighborhood or error message
    """
    if not isinstance(city, str) or not isinstance(neighborhood, str):
        logging.error("Invalid input: city and neighborhood must be strings")
        return {'error': 'Invalid input: city and neighborhood must be strings'}

    city = sanitize_input(city)
    neighborhood = sanitize_input(neighborhood)
    
    if not city or not neighborhood:
        logging.error("Empty input after sanitization")
        return {'error': 'City or neighborhood cannot be empty'}

    try:
        if city not in NEIGHBORHOODS:
            logging.error(f"City {city} not found")
            return {'error': f'City {city} not found'}

        for nb in NEIGHBORHOODS[city]:
            if nb['name'].lower() == neighborhood:
                population_density = nb['population'] / nb['area_sqkm'] if nb['area_sqkm'] > 0 else 0
                logging.info(f"Retrieved data for {nb['name']} in {city}")
                return {
                    'city': city.capitalize(),
                    'name': nb['name'],
                    'population': nb['population'],
                    'area_sqkm': nb['area_sqkm'],
                    'population_density': round(population_density, 2),
                    'safety_score': nb['safety_score'],
                    'traffic_score': nb['traffic_score'],
                    'schools': nb['schools'],
                    'hospitals': nb['hospitals'],
                    'future_growth': nb['future_growth'],
                    'avg_price_per_sqft': nb['avg_price_per_sqft'],
                    'info': f'Data for {nb["name"]} in {city.capitalize()}'
                }
        
        logging.error(f"Neighborhood {neighborhood} not found in {city}")
        return {'error': f'Neighborhood {neighborhood} not found in {city}'}
    except Exception as e:
        logging.error(f"Error accessing data: {str(e)}")
        return {'error': f'Internal error: {str(e)}'}

def list_neighborhoods(city):
    """
    List all neighborhoods for a given city.
    
    Args:
        city (str): Name of the city (e.g., 'Ahmedabad', 'Gandhinagar')
    
    Returns:
        dict: List of neighborhoods or error message
    """
    city = sanitize_input(city)
    if not city:
        logging.error("Empty city input after sanitization")
        return {'error': 'City cannot be empty'}

    try:
        if city not in NEIGHBORHOODS:
            logging.error(f"City {city} not found")
            return {'error': f'City {city} not found'}
        
        return {
            'city': city.capitalize(),
            'neighborhoods': [nb['name'] for nb in NEIGHBORHOODS[city]]
        }
    except Exception as e:
        logging.error(f"Error listing neighborhoods: {str(e)}")
        return {'error': f'Internal error: {str(e)}'}

def export_neighborhood_data(city, filename='neighborhood_data.json'):
    """
    Export neighborhood data for a city to a JSON file.
    
    Args:
        city (str): Name of the city
        filename (str): Name of the output JSON file
    
    Returns:
        dict: Success or error message
    """
    city = sanitize_input(city)
    if not city:
        logging.error("Empty city input after sanitization")
        return {'error': 'City cannot be empty'}

    try:
        if city not in NEIGHBORHOODS:
            logging.error(f"City {city} not found")
            return {'error': f'City {city} not found'}

        data = [
            {
                'name': nb['name'],
                'population': nb['population'],
                'area_sqkm': nb['area_sqkm'],
                'population_density': round(nb['population'] / nb['area_sqkm'], 2) if nb['area_sqkm'] > 0 else 0,
                'safety_score': nb['safety_score'],
                'traffic_score': nb['traffic_score'],
                'schools': nb['schools'],
                'hospitals': nb['hospitals'],
                'future_growth': nb['future_growth'],
                'avg_price_per_sqft': nb['avg_price_per_sqft']
            }
            for nb in NEIGHBORHOODS[city]
        ]

        with open(filename, 'w') as f:
            json.dump({'city': city.capitalize(), 'neighborhoods': data}, f, indent=4)
        
        logging.info(f"Data exported to {filename}")
        return {'success': f'Data exported to {filename}'}
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        return {'error': f'Failed to export data: {str(e)}'}

def build_prompt(location_info):
    """
    Build a prompt for DeepSeek API to generate a neighborhood scorecard.
    
    Args:
        location_info (dict): Dictionary with neighborhood data
    
    Returns:
        str: Formatted prompt string for API consumption
    """
    required_keys = ['name', 'safety_score', 'traffic_score', 'schools', 'hospitals', 'future_growth', 'avg_price_per_sqft']
    
    for key in required_keys:
        if key not in location_info:
            logging.error(f"Missing key in location_info: {key}")
            raise ValueError(f"Missing key in location_info: {key}")
    
    prompt = (
        f"Generate a detailed neighborhood scorecard for {location_info['name']}:\n"
        f"- Safety Score: {location_info['safety_score']} (out of 10)\n"
        f"- Traffic Score: {location_info['traffic_score']} (out of 10)\n"
        f"- Quality of Schools: {location_info['schools']}\n"
        f"- Quality of Hospitals: {location_info['hospitals']}\n"
        f"- Future Growth Potential: {location_info['future_growth']}\n"
        f"- Average Price per Square Foot: ₹{location_info['avg_price_per_sqft']}\n"
        f"Please provide actionable insights and a summary."
    )
    return prompt

def get_deepseek_scorecard(location_info):
    """
    Call DeepSeek API with neighborhood data prompt and get the generated scorecard.
    
    Args:
        location_info (dict): Dictionary with neighborhood data
    
    Returns:
        dict: API response with generated scorecard or error
    """
    if not DEEPSEEK_API_KEY:
        logging.error("DeepSeek API key not found in environment variables")
        return {'error': 'DeepSeek API key missing'}
    
    prompt = build_prompt(location_info)
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
        response.raise_for_status()
        result_json = response.json()
        
        if 'choices' in result_json and len(result_json['choices']) > 0:
            content = result_json['choices'][0]['message']['content']
            return {'scorecard': content}
        else:
            logging.error("Unexpected response structure from DeepSeek API")
            return {'error': 'Unexpected response format from DeepSeek API'}
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API request failed: {str(e)}")
        return {'error': f'DeepSeek API request failed: {str(e)}'}
