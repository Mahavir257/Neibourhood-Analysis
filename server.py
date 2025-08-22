"""
Enhanced Flask API Server for Neighborhood Analysis Tool
Provides comprehensive real estate analysis endpoints with caching and rate limiting
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import pandas as pd
from copy import deepcopy
import time
import hashlib
from functools import wraps
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
import logging

# Import our enhanced analysis modules
from deepseek_client import build_prompt, call_deepseek
from app import (
    get_neighborhood_info, get_investment_analysis, compare_locations,
    get_top_locations, export_analysis_report, analyzer
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Simple in-memory cache for API responses
cache = {}
CACHE_TIMEOUT = 300  # 5 minutes

# Rate limiting storage
rate_limit_storage = {}
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # 1 hour

def cache_response(timeout=CACHE_TIMEOUT):
    """Decorator to cache API responses"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Create cache key from endpoint and arguments
            cache_key = hashlib.md5(
                f"{request.endpoint}:{request.args}:{request.get_data()}".encode()
            ).hexdigest()
            
            # Check cache
            if cache_key in cache:
                cached_data, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    return cached_data
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator

def rate_limit(max_requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Initialize or clean old entries
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            
            # Remove old requests outside window
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip]
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per hour allowed'
                }), 429
            
            # Record this request
            rate_limit_storage[client_ip].append(current_time)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Load neighborhood data
try:
    with open("neighbourhood_data.json", "r", encoding="utf-8") as f:
        DATA = json.load(f)
    DF = pd.DataFrame(DATA)
    logging.info(f"Loaded {len(DATA)} neighborhoods successfully")
except Exception as e:
    logging.error(f"Error loading data: {e}")
    DATA = []
    DF = pd.DataFrame()

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'locations_loaded': len(DATA),
        'version': '2.0'
    })

# Enhanced locations endpoint
@app.route('/locations')
@cache_response(600)  # Cache for 10 minutes
def list_locations():
    """List all available locations with basic stats"""
    if not DATA:
        return jsonify({'error': 'No data available'}), 500
    
    locations = []
    for location in DATA:
        locations.append({
            'location': location['location'],
            'city': location['city'],
            'area': location['area'],
            'price_per_sqft': location['avg_price_per_sqft'],
            'safety_score': location['safety_score'],
            'investment_score': location.get('investment_score', 0)
        })
    
    # Sort by city then by area name
    locations.sort(key=lambda x: (x['city'], x['area']))
    
    return jsonify({
        'total_locations': len(locations),
        'cities': list(set(loc['city'] for loc in locations)),
        'locations': locations
    })

# Enhanced single location endpoint
@app.route('/location')
@cache_response()
@rate_limit()
def get_location():
    """Get comprehensive information for a single location"""
    location_name = request.args.get('name', '').strip()
    
    if not location_name:
        return jsonify({'error': 'Location name is required'}), 400
    
    try:
        result = get_neighborhood_info(location_name)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # Add real-time calculated metrics
        result['_metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'data_source': 'neighborhood_analysis_v2.0',
            'confidence_score': 0.95
        }
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error in get_location: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Investment analysis endpoint
@app.route('/investment-analysis', methods=['POST'])
@rate_limit()
def investment_analysis():
    """Comprehensive investment analysis for a location"""
    try:
        body = request.get_json(force=True)
        location = body.get('location', '')
        investment_amount = body.get('investment_amount', 10000000)
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        if investment_amount <= 0:
            return jsonify({'error': 'Investment amount must be positive'}), 400
        
        result = get_investment_analysis(location, investment_amount)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error in investment_analysis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Location comparison endpoint
@app.route('/compare', methods=['POST'])
@rate_limit()
def compare():
    """Compare multiple locations across various metrics"""
    try:
        body = request.get_json(force=True)
        locations = body.get('locations', [])
        
        if not locations or len(locations) < 2:
            return jsonify({'error': 'At least 2 locations required for comparison'}), 400
        
        if len(locations) > 5:
            return jsonify({'error': 'Maximum 5 locations allowed for comparison'}), 400
        
        result = compare_locations(locations)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error in compare: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Enhanced top picks endpoint
@app.route('/top-picks', methods=['GET', 'POST'])
@cache_response()
def top_picks():
    """Get top location picks based on various criteria"""
    try:
        if request.method == 'POST':
            params = request.get_json(force=True)
        else:
            params = request.args.to_dict()
        
        criteria = params.get('criteria', 'overall')
        budget_max = params.get('budget_max')
        city_filter = params.get('city_filter')
        limit = int(params.get('limit', 5))
        
        # Validate inputs
        if budget_max:
            budget_max = float(budget_max)
        
        if limit > 20:
            limit = 20  # Maximum 20 results
        
        result = get_top_locations(criteria, budget_max, city_filter, limit)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logging.error(f"Error in top_picks: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Market trends endpoint
@app.route('/market-trends')
@cache_response(900)  # Cache for 15 minutes
def market_trends():
    """Get market trends analysis"""
    try:
        city_filter = request.args.get('city')
        
        df = DF.copy()
        if city_filter:
            df = df[df['city'].str.lower() == city_filter.lower()]
        
        if df.empty:
            return jsonify({'error': 'No data available for specified city'}), 404
        
        # Calculate market statistics
        trends = {
            'market_overview': {
                'total_locations': len(df),
                'avg_price_per_sqft': round(df['avg_price_per_sqft'].mean(), 2),
                'price_range': {
                    'min': round(df['avg_price_per_sqft'].min(), 2),
                    'max': round(df['avg_price_per_sqft'].max(), 2)
                },
                'avg_safety_score': round(df['safety_score'].mean(), 2),
                'avg_rental_yield': round(df['rental_yield'].mean(), 2)
            },
            'growth_analysis': {
                'high_growth_areas': len(df[df['future_growth'] == 'High']),
                'medium_growth_areas': len(df[df['future_growth'] == 'Medium']),
                'low_growth_areas': len(df[df['future_growth'] == 'Low']),
                'avg_appreciation_rate': round(df['appreciation_rate'].mean(), 2)
            },
            'investment_hotspots': df.nlargest(3, 'investment_score')[['location', 'investment_score']].to_dict('records'),
            'most_affordable': df.nsmallest(3, 'avg_price_per_sqft')[['location', 'avg_price_per_sqft']].to_dict('records'),
            'safest_areas': df.nlargest(3, 'safety_score')[['location', 'safety_score']].to_dict('records')
        }
        
        return jsonify(trends)
    
    except Exception as e:
        logging.error(f"Error in market_trends: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Advanced search endpoint
@app.route('/search', methods=['POST'])
@rate_limit()
def advanced_search():
    """Advanced search with multiple filters"""
    try:
        filters = request.get_json(force=True)
        
        df = DF.copy()
        
        # Apply filters
        if 'min_safety_score' in filters:
            df = df[df['safety_score'] >= float(filters['min_safety_score'])]
        
        if 'max_traffic_score' in filters:
            df = df[df['traffic_score'] <= float(filters['max_traffic_score'])]
        
        if 'min_schools' in filters:
            df = df[df['schools'] >= int(filters['min_schools'])]
        
        if 'min_hospitals' in filters:
            df = df[df['hospitals'] >= int(filters['min_hospitals'])]
        
        if 'max_price_per_sqft' in filters:
            df = df[df['avg_price_per_sqft'] <= float(filters['max_price_per_sqft'])]
        
        if 'min_rental_yield' in filters:
            df = df[df['rental_yield'] >= float(filters['min_rental_yield'])]
        
        if 'future_growth' in filters and filters['future_growth'] != 'Any':
            df = df[df['future_growth'] == filters['future_growth']]
        
        if 'city' in filters:
            df = df[df['city'].str.lower() == filters['city'].lower()]
        
        if 'metro_required' in filters and filters['metro_required']:
            # Filter locations with metro connectivity
            df = df[df['metro'].apply(lambda x: x.get('available', False) if isinstance(x, dict) else False)]
        
        # Sort results
        sort_by = filters.get('sort_by', 'investment_score')
        if sort_by in df.columns:
            df = df.sort_values(sort_by, ascending=False)
        
        # Limit results
        limit = min(int(filters.get('limit', 10)), 50)
        results = df.head(limit)
        
        return jsonify({
            'total_found': len(df),
            'showing': len(results),
            'filters_applied': filters,
            'results': results.to_dict('records')
        })
    
    except Exception as e:
        logging.error(f"Error in advanced_search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# AI analysis endpoint (using DeepSeek)
@app.route('/ai-analysis', methods=['POST'])
@rate_limit(20, 3600)  # More restrictive rate limit for AI calls
def ai_analysis():
    """Generate AI-powered analysis for a location"""
    try:
        body = request.get_json(force=True)
        location_name = body.get('location', '')
        
        if not location_name:
            return jsonify({'error': 'Location name is required'}), 400
        
        # Get location data
        location_info = get_neighborhood_info(location_name)
        if 'error' in location_info:
            return jsonify(location_info), 404
        
        # Generate AI analysis
        prompt = build_prompt(location_info)
        ai_result = call_deepseek(prompt)
        
        return jsonify({
            'location': location_info['location'],
            'ai_analysis': ai_result,
            'generated_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error in ai_analysis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Export report endpoint
@app.route('/export-report', methods=['POST'])
@rate_limit(10, 3600)  # Limited exports per hour
def export_report():
    """Export comprehensive analysis report"""
    try:
        body = request.get_json(force=True)
        location = body.get('location', '')
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        result = export_analysis_report(location)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # Return the file path for download
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error in export_report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Download report file
@app.route('/download-report/<filename>')
def download_report(filename):
    """Download exported report file"""
    try:
        # Validate filename for security
        if not filename.endswith('.json') or '..' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        if not os.path.exists(filename):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filename, as_attachment=True)
    
    except Exception as e:
        logging.error(f"Error in download_report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Statistics endpoint
@app.route('/statistics')
@cache_response(1800)  # Cache for 30 minutes
def statistics():
    """Get comprehensive statistics about the data"""
    try:
        if DF.empty:
            return jsonify({'error': 'No data available'}), 500
        
        stats = {
            'data_overview': {
                'total_locations': len(DF),
                'cities': DF['city'].nunique(),
                'city_breakdown': DF['city'].value_counts().to_dict()
            },
            'price_statistics': {
                'average_price_per_sqft': round(DF['avg_price_per_sqft'].mean(), 2),
                'median_price_per_sqft': round(DF['avg_price_per_sqft'].median(), 2),
                'price_std_dev': round(DF['avg_price_per_sqft'].std(), 2),
                'most_expensive': DF.loc[DF['avg_price_per_sqft'].idxmax()]['location'],
                'most_affordable': DF.loc[DF['avg_price_per_sqft'].idxmin()]['location']
            },
            'safety_statistics': {
                'average_safety_score': round(DF['safety_score'].mean(), 2),
                'safest_location': DF.loc[DF['safety_score'].idxmax()]['location'],
                'safety_distribution': {
                    'excellent_9_plus': len(DF[DF['safety_score'] >= 9]),
                    'good_7_to_9': len(DF[(DF['safety_score'] >= 7) & (DF['safety_score'] < 9)]),
                    'average_5_to_7': len(DF[(DF['safety_score'] >= 5) & (DF['safety_score'] < 7)]),
                    'below_average_less_5': len(DF[DF['safety_score'] < 5])
                }
            },
            'investment_statistics': {
                'average_rental_yield': round(DF['rental_yield'].mean(), 2),
                'average_appreciation_rate': round(DF['appreciation_rate'].mean(), 2),
                'best_rental_yield': DF.loc[DF['rental_yield'].idxmax()]['location'],
                'best_appreciation': DF.loc[DF['appreciation_rate'].idxmax()]['location']
            },
            'infrastructure': {
                'locations_with_metro': len(DF[DF['metro'].apply(lambda x: x.get('available', False) if isinstance(x, dict) else False)]),
                'average_schools': round(DF['schools'].mean(), 1),
                'average_hospitals': round(DF['hospitals'].mean(), 1),
                'most_schools': DF.loc[DF['schools'].idxmax()]['location'],
                'most_hospitals': DF.loc[DF['hospitals'].idxmax()]['location']
            }
        }
        
        return jsonify(stats)
    
    except Exception as e:
        logging.error(f"Error in statistics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Cache management endpoints
@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear API response cache"""
    global cache
    cache.clear()
    return jsonify({'message': 'Cache cleared successfully'})

@app.route('/cache/stats')
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'cache_entries': len(cache),
        'cache_memory_usage': f"{len(str(cache))} characters"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# API documentation endpoint
@app.route('/api-docs')
def api_docs():
    """API documentation"""
    docs = {
        'version': '2.0',
        'title': 'Neighborhood Analysis API',
        'description': 'Comprehensive real estate analysis API for Ahmedabad and Gandhinagar',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /locations': 'List all available locations',
            'GET /location?name=<location>': 'Get detailed location information',
            'POST /investment-analysis': 'Get investment analysis for a location',
            'POST /compare': 'Compare multiple locations',
            'GET|POST /top-picks': 'Get top location recommendations',
            'GET /market-trends': 'Get market trends analysis',
            'POST /search': 'Advanced search with filters',
            'POST /ai-analysis': 'AI-powered location analysis',
            'POST /export-report': 'Export comprehensive analysis report',
            'GET /statistics': 'Get data statistics',
            'POST /cache/clear': 'Clear API cache',
            'GET /cache/stats': 'Get cache statistics'
        },
        'rate_limits': {
            'default': '100 requests/hour',
            'ai_analysis': '20 requests/hour',
            'export_report': '10 requests/hour'
        }
    }
    return jsonify(docs)

if __name__ == "__main__":
    # Clean up old cache entries on startup
    cache.clear()
    
    logging.info("Starting Enhanced Neighborhood Analysis API Server v2.0")
    logging.info(f"Loaded {len(DATA)} locations from {len(set(loc['city'] for loc in DATA))} cities")
    
    app.run(host="0.0.0.0", port=8000, debug=False)