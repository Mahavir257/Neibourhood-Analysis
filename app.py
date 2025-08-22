"""
Enhanced Neighborhood Analysis Tool for Ahmedabad & Gandhinagar
A comprehensive real estate analysis platform with AI-powered insights
"""

import logging
import json
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class InvestmentAnalysis:
    """Data class for investment analysis results"""
    roi_score: float
    risk_level: str
    expected_appreciation: float
    rental_yield_analysis: Dict
    market_trends: Dict
    investment_recommendation: str

@dataclass
class LocationComparison:
    """Data class for location comparison results"""
    locations: List[str]
    comparison_metrics: Dict
    winner_by_category: Dict
    overall_recommendation: str

class NeighborhoodAnalyzer:
    """Advanced neighborhood analysis engine"""
    
    def __init__(self, data_file: str = 'neighbourhood_data.json'):
        """Initialize with neighborhood data"""
        self.data_file = data_file
        self.neighborhoods = self._load_data()
        self.df = pd.DataFrame(self.neighborhoods)
        self._preprocess_data()
        
    def _load_data(self) -> List[Dict]:
        """Load neighborhood data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Loaded {len(data)} neighborhoods")
            return data
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return []
    
    def _preprocess_data(self):
        """Preprocess data and calculate derived metrics"""
        if self.df.empty:
            return
            
        # Calculate composite scores
        self.df['livability_score'] = (
            self.df['safety_score'] * 0.3 +
            self.df['infrastructure_score'] * 0.25 +
            self.df['lifestyle_score'] * 0.2 +
            self.df['environment_score'] * 0.15 +
            (10 - self.df['traffic_score']) * 0.1
        ).round(2)
        
        # Investment attractiveness score
        self.df['investment_attractiveness'] = (
            self.df['appreciation_rate'] * 0.4 +
            self.df['rental_yield'] * 10 * 0.3 +  # Convert to 10-point scale
            self.df['connectivity_score'] * 0.2 +
            self.df['investment_score'] * 0.1
        ).round(2)
        
        # Affordability index (inverse of price, normalized)
        max_price = self.df['avg_price_per_sqft'].max()
        min_price = self.df['avg_price_per_sqft'].min()
        price_range = max_price - min_price
        self.df['affordability_index'] = (
            (max_price - self.df['avg_price_per_sqft']) / price_range * 10
        ).round(2)
        
        logging.info("Data preprocessing completed")
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize and normalize input text"""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'[^a-zA-Z0-9\s,]', '', text)
        return ' '.join(text.strip().split()).lower()
    
    def get_neighborhood_info(self, location: str) -> Dict:
        """Get comprehensive information for a specific neighborhood"""
        location_clean = self.sanitize_input(location)
        
        if not location_clean:
            return {'error': 'Location cannot be empty'}
        
        # Find matching location
        matches = self.df[
            self.df['location'].str.lower().str.contains(location_clean, na=False) |
            self.df['area'].str.lower().str.contains(location_clean, na=False)
        ]
        
        if matches.empty:
            return {'error': f'Location "{location}" not found'}
        
        if len(matches) > 1:
            # Return list of matching locations for user to choose from
            return {
                'multiple_matches': True,
                'locations': matches['location'].tolist(),
                'message': 'Multiple locations found. Please be more specific.'
            }
        
        result = matches.iloc[0].to_dict()
        
        # Add calculated metrics
        result['calculated_metrics'] = {
            'livability_score': result.get('livability_score'),
            'investment_attractiveness': result.get('investment_attractiveness'),
            'affordability_index': result.get('affordability_index'),
            'population_density': result.get('population_density'),
            'price_per_sqft_rank': self._get_price_rank(result['avg_price_per_sqft']),
            'overall_rating': self._calculate_overall_rating(result)
        }
        
        return result
    
    def _get_price_rank(self, price: float) -> Dict:
        """Get price ranking information"""
        sorted_prices = self.df['avg_price_per_sqft'].sort_values()
        rank = (sorted_prices <= price).sum()
        total = len(sorted_prices)
        percentile = (rank / total) * 100
        
        if percentile <= 25:
            category = "Budget-friendly"
        elif percentile <= 50:
            category = "Moderate"
        elif percentile <= 75:
            category = "Premium"
        else:
            category = "Luxury"
            
        return {
            'rank': rank,
            'total_locations': total,
            'percentile': round(percentile, 1),
            'category': category
        }
    
    def _calculate_overall_rating(self, location_data: Dict) -> float:
        """Calculate overall rating for a location"""
        weights = {
            'safety_score': 0.20,
            'livability_score': 0.15,
            'investment_attractiveness': 0.15,
            'connectivity_score': 0.15,
            'infrastructure_score': 0.10,
            'lifestyle_score': 0.10,
            'environment_score': 0.10,
            'affordability_index': 0.05
        }
        
        total_score = sum(
            location_data.get(metric, 0) * weight 
            for metric, weight in weights.items()
        )
        
        return round(total_score, 2)
    
    def get_investment_analysis(self, location: str, investment_amount: float = 10000000) -> Dict:
        """Perform comprehensive investment analysis"""
        location_info = self.get_neighborhood_info(location)
        
        if 'error' in location_info or 'multiple_matches' in location_info:
            return location_info
        
        # Calculate investment metrics
        price_per_sqft = location_info['avg_price_per_sqft']
        rental_yield = location_info['rental_yield']
        appreciation_rate = location_info['appreciation_rate']
        
        # Investment calculations
        area_possible = investment_amount / price_per_sqft  # sq ft
        monthly_rental = (investment_amount * rental_yield / 100) / 12
        yearly_appreciation = investment_amount * (appreciation_rate / 100)
        
        # Risk assessment
        risk_factors = []
        risk_score = 0
        
        if location_info['traffic_score'] > 7:
            risk_factors.append("High traffic congestion")
            risk_score += 1
        
        if location_info['safety_score'] < 7:
            risk_factors.append("Below average safety")
            risk_score += 2
        
        if appreciation_rate < 5:
            risk_factors.append("Low appreciation rate")
            risk_score += 1
        
        if rental_yield < 3:
            risk_factors.append("Low rental yield")
            risk_score += 1
        
        # Risk level determination
        if risk_score <= 1:
            risk_level = "Low Risk"
        elif risk_score <= 3:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        
        # ROI Analysis
        annual_rental_income = monthly_rental * 12
        total_annual_return = annual_rental_income + yearly_appreciation
        roi_percentage = (total_annual_return / investment_amount) * 100
        
        # Market trends simulation
        market_trends = self._analyze_market_trends(location_info)
        
        # Investment recommendation
        if roi_percentage > 12 and risk_level == "Low Risk":
            recommendation = "Highly Recommended"
        elif roi_percentage > 10 and risk_level in ["Low Risk", "Medium Risk"]:
            recommendation = "Recommended"
        elif roi_percentage > 8:
            recommendation = "Consider with Caution"
        else:
            recommendation = "Not Recommended"
        
        return {
            'location': location_info['location'],
            'investment_amount': investment_amount,
            'analysis': {
                'area_purchased_sqft': round(area_possible, 2),
                'monthly_rental_income': round(monthly_rental, 2),
                'yearly_appreciation': round(yearly_appreciation, 2),
                'total_annual_return': round(total_annual_return, 2),
                'roi_percentage': round(roi_percentage, 2),
                'payback_period_years': round(investment_amount / total_annual_return, 1),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendation': recommendation
            },
            'market_trends': market_trends,
            'comparable_locations': self._get_comparable_investments(location_info)
        }
    
    def _analyze_market_trends(self, location_data: Dict) -> Dict:
        """Analyze market trends for the location"""
        # Simulate market trend analysis based on location characteristics
        growth_potential = location_data.get('future_growth', 'Medium')
        infrastructure_score = location_data.get('infrastructure_score', 5)
        connectivity_score = location_data.get('connectivity_score', 5)
        
        trend_score = 0
        if growth_potential == 'High':
            trend_score += 3
        elif growth_potential == 'Medium':
            trend_score += 2
        else:
            trend_score += 1
            
        if infrastructure_score > 8:
            trend_score += 2
        elif infrastructure_score > 6:
            trend_score += 1
            
        if connectivity_score > 8:
            trend_score += 2
        elif connectivity_score > 6:
            trend_score += 1
        
        if trend_score >= 6:
            outlook = "Very Positive"
            growth_forecast = "15-20% over next 3 years"
        elif trend_score >= 4:
            outlook = "Positive"
            growth_forecast = "10-15% over next 3 years"
        elif trend_score >= 2:
            outlook = "Stable"
            growth_forecast = "5-10% over next 3 years"
        else:
            outlook = "Uncertain"
            growth_forecast = "0-5% over next 3 years"
        
        return {
            'market_outlook': outlook,
            'price_growth_forecast': growth_forecast,
            'trend_score': trend_score,
            'key_drivers': self._identify_growth_drivers(location_data)
        }
    
    def _identify_growth_drivers(self, location_data: Dict) -> List[str]:
        """Identify key growth drivers for the location"""
        drivers = []
        
        if location_data.get('metro', {}).get('available'):
            drivers.append("Metro connectivity")
        
        if location_data.get('infrastructure_score', 0) > 8:
            drivers.append("Excellent infrastructure")
        
        if location_data.get('schools', 0) > 15:
            drivers.append("Educational hub")
        
        if location_data.get('connectivity_score', 0) > 8:
            drivers.append("Strategic location")
        
        if location_data.get('lifestyle_score', 0) > 8:
            drivers.append("Premium lifestyle amenities")
        
        return drivers
    
    def _get_comparable_investments(self, location_data: Dict) -> List[Dict]:
        """Get comparable investment opportunities"""
        current_price = location_data['avg_price_per_sqft']
        current_city = location_data['city']
        
        # Find locations with similar price range (±20%)
        price_lower = current_price * 0.8
        price_upper = current_price * 1.2
        
        comparables = self.df[
            (self.df['avg_price_per_sqft'] >= price_lower) &
            (self.df['avg_price_per_sqft'] <= price_upper) &
            (self.df['location'] != location_data['location'])
        ].head(3)
        
        result = []
        for _, comp in comparables.iterrows():
            result.append({
                'location': comp['location'],
                'price_per_sqft': comp['avg_price_per_sqft'],
                'rental_yield': comp['rental_yield'],
                'appreciation_rate': comp['appreciation_rate'],
                'investment_score': comp['investment_score']
            })
        
        return result
    
    def compare_locations(self, locations: List[str]) -> Dict:
        """Compare multiple locations across various metrics"""
        if len(locations) < 2:
            return {'error': 'At least 2 locations required for comparison'}
        
        comparison_data = []
        not_found = []
        
        for location in locations:
            info = self.get_neighborhood_info(location)
            if 'error' in info:
                not_found.append(location)
            else:
                comparison_data.append(info)
        
        if len(comparison_data) < 2:
            return {'error': f'Could not find enough valid locations. Not found: {not_found}'}
        
        # Comparison metrics
        metrics = [
            'safety_score', 'traffic_score', 'schools', 'hospitals',
            'avg_price_per_sqft', 'rental_yield', 'appreciation_rate',
            'connectivity_score', 'infrastructure_score', 'lifestyle_score',
            'environment_score', 'investment_score'
        ]
        
        comparison_result = {
            'locations': [loc['location'] for loc in comparison_data],
            'metrics': {},
            'winners': {},
            'summary': {}
        }
        
        # Compare each metric
        for metric in metrics:
            values = [loc.get(metric, 0) for loc in comparison_data]
            comparison_result['metrics'][metric] = {
                loc['location']: loc.get(metric, 0) for loc in comparison_data
            }
            
            # Determine winner (higher is better for most metrics, except traffic_score and avg_price_per_sqft)
            if metric in ['traffic_score', 'avg_price_per_sqft']:
                best_idx = values.index(min(values))
            else:
                best_idx = values.index(max(values))
            
            comparison_result['winners'][metric] = comparison_data[best_idx]['location']
        
        # Overall recommendation
        scores = []
        for loc in comparison_data:
            score = loc['calculated_metrics']['overall_rating']
            scores.append(score)
        
        best_overall_idx = scores.index(max(scores))
        comparison_result['overall_winner'] = comparison_data[best_overall_idx]['location']
        
        # Generate summary insights
        comparison_result['summary'] = self._generate_comparison_summary(comparison_data, comparison_result)
        
        return comparison_result
    
    def _generate_comparison_summary(self, locations_data: List[Dict], comparison_result: Dict) -> Dict:
        """Generate intelligent summary of location comparison"""
        summary = {
            'best_for_safety': comparison_result['winners']['safety_score'],
            'best_for_investment': comparison_result['winners']['appreciation_rate'],
            'most_affordable': comparison_result['winners']['avg_price_per_sqft'],
            'best_connectivity': comparison_result['winners']['connectivity_score'],
            'best_lifestyle': comparison_result['winners']['lifestyle_score'],
            'recommendations': {}
        }
        
        # Generate specific recommendations
        for loc_data in locations_data:
            location = loc_data['location']
            recommendations = []
            
            if loc_data['safety_score'] >= 9:
                recommendations.append("Excellent for families with children")
            
            if loc_data['appreciation_rate'] >= 10:
                recommendations.append("High investment potential")
            
            if loc_data['avg_price_per_sqft'] <= 6000:
                recommendations.append("Budget-friendly option")
            
            if loc_data['lifestyle_score'] >= 9:
                recommendations.append("Premium lifestyle destination")
            
            if loc_data['connectivity_score'] >= 9:
                recommendations.append("Excellent for professionals")
            
            summary['recommendations'][location] = recommendations
        
        return summary
    
    def get_top_locations(self, 
                         criteria: str = 'overall',
                         budget_max: Optional[float] = None,
                         city_filter: Optional[str] = None,
                         limit: int = 5) -> Dict:
        """Get top locations based on specified criteria"""
        
        df_filtered = self.df.copy()
        
        # Apply filters
        if budget_max:
            df_filtered = df_filtered[df_filtered['avg_price_per_sqft'] <= budget_max]
        
        if city_filter:
            df_filtered = df_filtered[df_filtered['city'].str.lower() == city_filter.lower()]
        
        if df_filtered.empty:
            return {'error': 'No locations match the specified criteria'}
        
        # Sort based on criteria
        if criteria == 'investment':
            sort_column = 'investment_attractiveness'
        elif criteria == 'safety':
            sort_column = 'safety_score'
        elif criteria == 'affordability':
            sort_column = 'affordability_index'
        elif criteria == 'lifestyle':
            sort_column = 'lifestyle_score'
        elif criteria == 'connectivity':
            sort_column = 'connectivity_score'
        else:  # overall
            sort_column = 'livability_score'
        
        top_locations = df_filtered.nlargest(limit, sort_column)
        
        result = {
            'criteria': criteria,
            'total_found': len(df_filtered),
            'showing_top': min(limit, len(top_locations)),
            'locations': []
        }
        
        for _, loc in top_locations.iterrows():
            result['locations'].append({
                'location': loc['location'],
                'city': loc['city'],
                'score': loc[sort_column],
                'price_per_sqft': loc['avg_price_per_sqft'],
                'key_highlights': self._get_key_highlights(loc)
            })
        
        return result
    
    def _get_key_highlights(self, location_data: pd.Series) -> List[str]:
        """Get key highlights for a location"""
        highlights = []
        
        if location_data['safety_score'] >= 9:
            highlights.append(f"Excellent Safety Score: {location_data['safety_score']}/10")
        
        if location_data['metro'].get('available', False) if isinstance(location_data['metro'], dict) else False:
            highlights.append("Metro Connectivity Available")
        
        if location_data['appreciation_rate'] >= 10:
            highlights.append(f"High Appreciation: {location_data['appreciation_rate']}%")
        
        if location_data['schools'] >= 15:
            highlights.append("Educational Hub")
        
        if location_data['lifestyle_score'] >= 9:
            highlights.append("Premium Lifestyle Amenities")
        
        return highlights[:3]  # Return top 3 highlights
    
    def export_analysis_report(self, location: str, filename: Optional[str] = None) -> Dict:
        """Export comprehensive analysis report"""
        if not filename:
            safe_location = re.sub(r'[^a-zA-Z0-9]', '_', location)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'analysis_report_{safe_location}_{timestamp}.json'
        
        try:
            # Get comprehensive data
            location_info = self.get_neighborhood_info(location)
            if 'error' in location_info:
                return location_info
            
            investment_analysis = self.get_investment_analysis(location)
            
            # Create comprehensive report
            report = {
                'report_metadata': {
                    'location': location,
                    'generated_at': datetime.now().isoformat(),
                    'report_version': '1.0'
                },
                'location_overview': location_info,
                'investment_analysis': investment_analysis,
                'market_position': self._get_market_position(location_info),
                'recommendations': self._get_detailed_recommendations(location_info)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Analysis report exported to {filename}")
            return {'success': f'Report exported to {filename}', 'filename': filename}
        
        except Exception as e:
            logging.error(f"Error exporting report: {str(e)}")
            return {'error': f'Failed to export report: {str(e)}'}
    
    def _get_market_position(self, location_data: Dict) -> Dict:
        """Get market position analysis"""
        city = location_data['city']
        city_locations = self.df[self.df['city'] == city]
        
        # Calculate rankings within city
        price_rank = (city_locations['avg_price_per_sqft'] <= location_data['avg_price_per_sqft']).sum()
        safety_rank = (city_locations['safety_score'] <= location_data['safety_score']).sum()
        investment_rank = (city_locations['investment_attractiveness'] <= location_data['calculated_metrics']['investment_attractiveness']).sum()
        
        total_city_locations = len(city_locations)
        
        return {
            'city': city,
            'total_locations_in_city': total_city_locations,
            'price_rank': f"{price_rank}/{total_city_locations}",
            'safety_rank': f"{safety_rank}/{total_city_locations}",
            'investment_rank': f"{investment_rank}/{total_city_locations}",
            'percentile_rankings': {
                'price': round((price_rank / total_city_locations) * 100, 1),
                'safety': round((safety_rank / total_city_locations) * 100, 1),
                'investment': round((investment_rank / total_city_locations) * 100, 1)
            }
        }
    
    def _get_detailed_recommendations(self, location_data: Dict) -> Dict:
        """Get detailed recommendations based on location analysis"""
        recommendations = {
            'target_demographics': [],
            'investment_strategy': [],
            'lifestyle_benefits': [],
            'potential_concerns': []
        }
        
        # Target demographics
        if location_data['schools'] >= 15 and location_data['safety_score'] >= 8:
            recommendations['target_demographics'].append("Families with school-age children")
        
        if location_data['connectivity_score'] >= 8:
            recommendations['target_demographics'].append("Working professionals")
        
        if location_data['lifestyle_score'] >= 8.5:
            recommendations['target_demographics'].append("Affluent individuals seeking premium lifestyle")
        
        # Investment strategy
        if location_data['appreciation_rate'] >= 10:
            recommendations['investment_strategy'].append("Buy and hold for capital appreciation")
        
        if location_data['rental_yield'] >= 3.5:
            recommendations['investment_strategy'].append("Rental income generation strategy")
        
        if location_data['future_growth'] == 'High':
            recommendations['investment_strategy'].append("Long-term growth investment")
        
        # Lifestyle benefits
        if location_data.get('metro', {}).get('available'):
            recommendations['lifestyle_benefits'].append("Excellent public transportation")
        
        if location_data['environment_score'] >= 8:
            recommendations['lifestyle_benefits'].append("Clean and green environment")
        
        if len(location_data.get('amenities', {}).get('malls', [])) >= 2:
            recommendations['lifestyle_benefits'].append("Shopping and entertainment options")
        
        # Potential concerns
        if location_data['traffic_score'] >= 7:
            recommendations['potential_concerns'].append("High traffic congestion during peak hours")
        
        if location_data['avg_price_per_sqft'] >= 7500:
            recommendations['potential_concerns'].append("High property prices may limit affordability")
        
        if location_data['safety_score'] < 8:
            recommendations['potential_concerns'].append("Safety measures may need attention")
        
        return recommendations

# Global analyzer instance
analyzer = NeighborhoodAnalyzer()

def get_neighborhood_info(location: str) -> Dict:
    """Get comprehensive neighborhood information"""
    return analyzer.get_neighborhood_info(location)

def get_investment_analysis(location: str, investment_amount: float = 10000000) -> Dict:
    """Get investment analysis for a location"""
    return analyzer.get_investment_analysis(location, investment_amount)

def compare_locations(locations: List[str]) -> Dict:
    """Compare multiple locations"""
    return analyzer.compare_locations(locations)

def get_top_locations(criteria: str = 'overall', budget_max: Optional[float] = None, 
                     city_filter: Optional[str] = None, limit: int = 5) -> Dict:
    """Get top locations based on criteria"""
    return analyzer.get_top_locations(criteria, budget_max, city_filter, limit)

def export_analysis_report(location: str, filename: Optional[str] = None) -> Dict:
    """Export comprehensive analysis report"""
    return analyzer.export_analysis_report(location, filename)

# Example usage and testing
if __name__ == '__main__':
    # Test basic functionality
    print("=== Neighborhood Analysis Tool ===")
    
    # Test 1: Get neighborhood info
    print("\n1. Getting info for Satellite, Ahmedabad:")
    result = get_neighborhood_info("Satellite")
    print(f"Location: {result.get('location', 'Not found')}")
    if 'calculated_metrics' in result:
        print(f"Overall Rating: {result['calculated_metrics']['overall_rating']}/10")
    
    # Test 2: Investment analysis
    print("\n2. Investment analysis for Vastrapur:")
    investment_result = get_investment_analysis("Vastrapur", 20000000)
    if 'analysis' in investment_result:
        print(f"ROI: {investment_result['analysis']['roi_percentage']}%")
        print(f"Recommendation: {investment_result['analysis']['recommendation']}")
    
    # Test 3: Location comparison
    print("\n3. Comparing Satellite vs Vastrapur:")
    comparison = compare_locations(["Satellite", "Vastrapur"])
    if 'overall_winner' in comparison:
        print(f"Overall Winner: {comparison['overall_winner']}")
    
    # Test 4: Top locations
    print("\n4. Top 3 locations for investment:")
    top_locations = get_top_locations('investment', limit=3)
    if 'locations' in top_locations:
        for i, loc in enumerate(top_locations['locations'], 1):
            print(f"{i}. {loc['location']} (Score: {loc['score']})")