ahmedabad_gandhinagar_neighbourhood_pro_tool.py
Enhanced neighborhood analysis tool with additional features
import loggingimport jsonimport re
Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def sanitize_input(text):    """    Sanitize input by removing extra whitespace and special characters.
Args:
    text (str): Input string to sanitize

Returns:
    str: Sanitized string
"""
if not isinstance(text, str):
    return ""
# Remove special characters, keep alphanumeric and spaces
text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
# Remove extra whitespace
return ' '.join(text.strip().split())

def get_neighborhood_info(city, neighborhood):    """    Retrieve neighborhood information for Ahmedabad or Gandhinagar with case-insensitive matching.
Args:
    city (str): Name of the city (e.g., 'Ahmedabad', 'Gandhinagar')
    neighborhood (str): Name of the neighborhood

Returns:
    dict: Detailed information about the neighborhood or error message
"""
# Input validation
if not isinstance(city, str) or not isinstance(neighborhood, str):
    logging.error("Invalid input: city and neighborhood must be strings")
    return {'error': 'Invalid input: city and neighborhood must be strings'}

city = sanitize_input(city)
neighborhood = sanitize_input(neighborhood)

if not city or not neighborhood:
    logging.error("Empty input after sanitization")
    return {'error': 'City or neighborhood cannot be empty'}

# Sample data; replace with actual data source (e.g., API or database)
neighborhoods = {
    'ahmedabad': [
        {'name': 'Navrangpura', 'population': 50000, 'area_sqkm': 5.2},
        {'name': 'Vastrapur', 'population': 45000, 'area_sqkm': 4.8},
        {'name': 'Maninagar', 'population': 60000, 'area_sqkm': 6.0}
    ],
    'gandhinagar': [
        {'name': 'Sector 21', 'population': 20000, 'area_sqkm': 3.5},
        {'name': 'Sector 7', 'population': 18000, 'area_sqkm': 3.0},
        {'name': 'Kudasan', 'population': 25000, 'area_sqkm': 4.0}
    ]
}

try:
    # Convert inputs to lowercase for case-insensitive matching
    city = city.lower()
    neighborhood = neighborhood.lower()

    if city not in neighborhoods:
        logging.error(f"City {city} not found")
        return {'error': f'City {city} not found'}

    # Find the neighborhood in the city's list
    for nb in neighborhoods[city]:
        if nb['name'].lower() == neighborhood:
            population_density = nb['population'] / nb['area_sqkm'] if nb['area_sqkm'] > 0 else 0
            logging.info(f"Retrieved data for {nb['name']} in {city}")
            return {
                'city': city.capitalize(),
                'neighborhood': nb['name'],
                'population': nb['population'],
                'area_sqkm': nb['area_sqkm'],
                'population_density': round(population_density, 2),
                'info': f'Data for {nb["name"]} in {city.capitalize()}'
            }

    logging.error(f"Neighborhood {neighborhood} not found in {city}")
    return {'error': f'Neighborhood {neighborhood} not found in {city}'}

except Exception as e:
    logging.error(f"Error accessing data: {str(e)}")
    return {'error': f'Internal error: {str(e)}'}

def list_neighborhoods(city):    """    List all neighborhoods for a given city.
Args:
    city (str): Name of the city (e.g., 'Ahmedabad', 'Gandhinagar')

Returns:
    dict: List of neighborhoods or error message
"""
city = sanitize_input(city)
if not city:
    logging.error("Empty city input after sanitization")
    return {'error': 'City cannot be empty'}

neighborhoods = {
    'ahmedabad': [
        {'name': 'Navrangpura', 'population': 50000, 'area_sqkm': 5.2},
        {'name': 'Vastrapur', 'population': 45000, 'area_sqkm': 4.8},
        {'name': 'Maninagar', 'population': 60000, 'area_sqkm': 6.0}
    ],
    'gandhinagar': [
        {'name': 'Sector 21', 'population': 20000, 'area_sqkm': 3.5},
        {'name': 'Sector 7', 'population': 18000, 'area_sqkm': 3.0},
        {'name': 'Kudasan', 'population': 25000, 'area_sqkm': 4.0}
    ]
}

try:
    city = city.lower()
    if city not in neighborhoods:
        logging.error(f"City {city} not found")
        return {'error': f'City {city} not found'}

    return {
        'city': city.capitalize(),
        'neighborhoods': [nb['name'] for nb in neighborhoods[city]]
    }

except Exception as e:
    logging.error(f"Error listing neighborhoods: {str(e)}")
    return {'error': f'Internal error: {str(e)}'}

def export_neighborhood_data(city, filename='neighborhood_data.json'):    """    Export neighborhood data for a city to a JSON file.
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

neighborhoods = {
    'ahmedabad': [
        {'name': 'Navrangpura', 'population': 50000, 'area_sqkm': 5.2},
        {'name': 'Vastrapur', 'population': 45000, 'area_sqkm': 4.8},
        {'name': 'Maninagar', 'population': 60000, 'area_sqkm': 6.0}
    ],
    'gandhinagar': [
        {'name': 'Sector 21', 'population': 20000, 'area_sqkm': 3.5},
        {'name': 'Sector 7', 'population': 18000, 'area_sqkm': 3.0},
        {'name': 'Kudasan', 'population': 25000, 'area_sqkm': 4.0}
    ]
}

try:
    city = city.lower()
    if city not in neighborhoods:
        logging.error(f"City {city} not found")
        return {'error': f'City {city} not found'}

    # Calculate population density for each neighborhood
    data = [
        {
            'name': nb['name'],
            'population': nb['population'],
            'area_sqkm': nb['area_sqkm'],
            'population_density': round(nb['population'] / nb['area_sqkm'], 2) if nb['area_sqkm'] > 0 else 0
        }
        for nb in neighborhoods[city]
    ]

    with open(filename, 'w') as f:
        json.dump({'city': city.capitalize(), 'neighborhoods': data}, f, indent=4)
    logging.info(f"Data exported to {filename}")
    return {'success': f'Data exported to {filename}'}

except Exception as e:
    logging.error(f"Error exporting data: {str(e)}")
    return {'error': f'Failed to export data: {str(e)}'}

Example usage
if name == 'main':    # Get info for a specific neighborhood    result1 = get_neighborhood_info('Ahmedabad  ', ' Navrangpura! ')    print("Neighborhood Info:", result1)
# List all neighborhoods in a city
result2 = list_neighborhoods('Gandhinagar')
print("Neighborhood List:", result2)

# Export data to JSON
result3 = export_neighborhood_data('Ahmedabad')
print("Export Result:", result3)
