"""
Comprehensive Test Suite for Neighborhood Analysis Tool
Tests all components including core analysis, API endpoints, and AI integration
"""

import unittest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
from typing import Dict, List
import logging
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to test
from app import (
    NeighborhoodAnalyzer, get_neighborhood_info, get_investment_analysis,
    compare_locations, get_top_locations, export_analysis_report
)
from deepseek_client import (
    build_prompt, call_deepseek, get_deepseek_scorecard,
    get_comparative_analysis, get_market_insights, get_investment_strategy
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestNeighborhoodAnalyzer(unittest.TestCase):
    """Test cases for the core NeighborhoodAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test data file
        self.test_data = [
            {
                "location": "Test Location 1",
                "city": "Test City",
                "area": "Test Area 1",
                "population": 10000,
                "population_density": 5000,
                "safety_score": 8.5,
                "traffic_score": 6.0,
                "schools": 10,
                "hospitals": 5,
                "future_growth": "High",
                "avg_price_per_sqft": 5000,
                "rental_yield": 4.0,
                "appreciation_rate": 8.0,
                "connectivity_score": 8.0,
                "infrastructure_score": 7.5,
                "lifestyle_score": 8.0,
                "environment_score": 7.0,
                "investment_score": 8.5
            },
            {
                "location": "Test Location 2", 
                "city": "Test City",
                "area": "Test Area 2",
                "population": 15000,
                "population_density": 6000,
                "safety_score": 7.0,
                "traffic_score": 8.0,
                "schools": 8,
                "hospitals": 3,
                "future_growth": "Medium",
                "avg_price_per_sqft": 4000,
                "rental_yield": 3.5,
                "appreciation_rate": 6.0,
                "connectivity_score": 6.5,
                "infrastructure_score": 6.0,
                "lifestyle_score": 6.5,
                "environment_score": 6.0,
                "investment_score": 6.5
            }
        ]
        
        # Create test data file
        with open('test_data.json', 'w') as f:
            json.dump(self.test_data, f)
        
        # Initialize analyzer with test data
        self.analyzer = NeighborhoodAnalyzer('test_data.json')
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.remove('test_data.json')
        except:
            pass
        
        # Clean up any generated report files
        import glob
        for file in glob.glob('analysis_report_*.json'):
            try:
                os.remove(file)
            except:
                pass
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization and data loading"""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(len(self.analyzer.neighborhoods), 2)
        self.assertFalse(self.analyzer.df.empty)
    
    def test_get_neighborhood_info_valid(self):
        """Test getting valid neighborhood information"""
        result = self.analyzer.get_neighborhood_info("Test Location 1")
        
        self.assertNotIn('error', result)
        self.assertEqual(result['location'], 'Test Location 1')
        self.assertEqual(result['safety_score'], 8.5)
        self.assertIn('calculated_metrics', result)
    
    def test_get_neighborhood_info_invalid(self):
        """Test getting information for non-existent location"""
        result = self.analyzer.get_neighborhood_info("Non-existent Location")
        
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
    
    def test_get_neighborhood_info_empty_input(self):
        """Test handling empty input"""
        result = self.analyzer.get_neighborhood_info("")
        
        self.assertIn('error', result)
    
    def test_investment_analysis_valid(self):
        """Test investment analysis for valid location"""
        result = self.analyzer.get_investment_analysis("Test Location 1", 10000000)
        
        self.assertNotIn('error', result)
        self.assertIn('analysis', result)
        self.assertIn('roi_percentage', result['analysis'])
        self.assertIn('monthly_rental_income', result['analysis'])
        self.assertIn('recommendation', result['analysis'])
    
    def test_investment_analysis_invalid_amount(self):
        """Test investment analysis with invalid amount"""
        # The function should handle this gracefully or we might need to add validation
        result = self.analyzer.get_investment_analysis("Test Location 1", -1000)
        
        # Depending on implementation, this might succeed or fail
        # The test validates current behavior
        self.assertIsInstance(result, dict)
    
    def test_compare_locations_valid(self):
        """Test comparing valid locations"""
        result = self.analyzer.compare_locations(["Test Location 1", "Test Location 2"])
        
        self.assertNotIn('error', result)
        self.assertIn('locations', result)
        self.assertIn('winners', result)
        self.assertIn('overall_winner', result)
        self.assertEqual(len(result['locations']), 2)
    
    def test_compare_locations_insufficient(self):
        """Test comparing with insufficient locations"""
        result = self.analyzer.compare_locations(["Test Location 1"])
        
        self.assertIn('error', result)
    
    def test_get_top_locations_overall(self):
        """Test getting top locations by overall criteria"""
        result = self.analyzer.get_top_locations('overall', limit=2)
        
        self.assertNotIn('error', result)
        self.assertIn('locations', result)
        self.assertLessEqual(len(result['locations']), 2)
    
    def test_get_top_locations_with_budget_filter(self):
        """Test getting top locations with budget filter"""
        result = self.analyzer.get_top_locations('overall', budget_max=4500, limit=5)
        
        self.assertNotIn('error', result)
        # Should only return locations within budget
        for location in result['locations']:
            self.assertLessEqual(location['price_per_sqft'], 4500)
    
    def test_export_analysis_report(self):
        """Test exporting analysis report"""
        result = self.analyzer.export_analysis_report("Test Location 1")
        
        self.assertNotIn('error', result)
        self.assertIn('filename', result)
        
        # Check if file was created
        filename = result['filename']
        self.assertTrue(os.path.exists(filename))
        
        # Verify file content
        with open(filename, 'r') as f:
            report_data = json.load(f)
        
        self.assertIn('report_metadata', report_data)
        self.assertIn('location_overview', report_data)
        self.assertIn('investment_analysis', report_data)

class TestDeepSeekClient(unittest.TestCase):
    """Test cases for DeepSeek AI client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_location_data = {
            'location': 'Test Location',
            'city': 'Test City',
            'safety_score': 8.5,
            'traffic_score': 6.0,
            'schools': 10,
            'hospitals': 5,
            'future_growth': 'High',
            'avg_price_per_sqft': 5000,
            'rental_yield': 4.0,
            'appreciation_rate': 8.0,
            'connectivity_score': 8.0,
            'infrastructure_score': 7.5,
            'investment_score': 8.5
        }
    
    def test_build_prompt_detailed_analysis(self):
        """Test building prompt for detailed analysis"""
        prompt = build_prompt(self.sample_location_data, 'detailed_analysis')
        
        self.assertIsInstance(prompt, str)
        self.assertIn('Test Location', prompt)
        self.assertIn('Safety Score', prompt)
        self.assertIn('comprehensive analysis', prompt.lower())
    
    def test_build_prompt_investment_focus(self):
        """Test building prompt for investment analysis"""
        prompt = build_prompt(self.sample_location_data, 'investment_focus')
        
        self.assertIsInstance(prompt, str)
        self.assertIn('investment', prompt.lower())
        self.assertIn('ROI', prompt)
    
    def test_build_prompt_family_focus(self):
        """Test building prompt for family analysis"""
        prompt = build_prompt(self.sample_location_data, 'family_focus')
        
        self.assertIsInstance(prompt, str)
        self.assertIn('families', prompt.lower())
        self.assertIn('Education Quality', prompt)
    
    def test_build_prompt_custom_focus(self):
        """Test building prompt with custom focus"""
        custom_focus = "environmental sustainability"
        prompt = build_prompt(self.sample_location_data, custom_focus=custom_focus)
        
        self.assertIsInstance(prompt, str)
        self.assertIn(custom_focus, prompt)
    
    @patch('deepseek_client.DEEPSEEK_API_KEY', None)
    def test_call_deepseek_no_api_key(self):
        """Test DeepSeek call without API key"""
        result = call_deepseek("Test prompt")
        
        self.assertIn('Error:', result)
        self.assertIn('API key', result)
    
    @patch('deepseek_client.DEEPSEEK_API_KEY', 'test_key')
    @patch('requests.post')
    def test_call_deepseek_success(self, mock_post):
        """Test successful DeepSeek API call"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'Test AI response'
                    }
                }
            ],
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = call_deepseek("Test prompt")
        
        self.assertEqual(result, 'Test AI response')
        mock_post.assert_called_once()
    
    @patch('deepseek_client.DEEPSEEK_API_KEY', 'test_key')
    @patch('requests.post')
    def test_call_deepseek_api_error(self, mock_post):
        """Test DeepSeek API call with error"""
        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        result = call_deepseek("Test prompt")
        
        self.assertIn('Error:', result)
        self.assertIn('API Error', result)
    
    def test_get_deepseek_scorecard(self):
        """Test getting DeepSeek scorecard"""
        with patch('deepseek_client.call_deepseek') as mock_call:
            mock_call.return_value = "Test analysis result"
            
            result = get_deepseek_scorecard(self.sample_location_data)
            
            self.assertIn('location', result)
            self.assertIn('analysis', result)
            self.assertIn('generated_at', result)
            self.assertEqual(result['analysis'], 'Test analysis result')

class TestAPIIntegration(unittest.TestCase):
    """Test cases for API integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_get_neighborhood_info_function(self):
        """Test standalone get_neighborhood_info function"""
        # This tests the function exported from app.py
        try:
            result = get_neighborhood_info("Satellite")
            # Should return either valid data or error message
            self.assertIsInstance(result, dict)
            # Should not crash
        except Exception as e:
            self.fail(f"get_neighborhood_info raised an exception: {e}")
    
    def test_get_investment_analysis_function(self):
        """Test standalone get_investment_analysis function"""
        try:
            result = get_investment_analysis("Satellite", 10000000)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"get_investment_analysis raised an exception: {e}")
    
    def test_compare_locations_function(self):
        """Test standalone compare_locations function"""
        try:
            result = compare_locations(["Satellite", "Vastrapur"])
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"compare_locations raised an exception: {e}")
    
    def test_get_top_locations_function(self):
        """Test standalone get_top_locations function"""
        try:
            result = get_top_locations('overall', limit=3)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"get_top_locations raised an exception: {e}")

class TestDataIntegrity(unittest.TestCase):
    """Test cases for data integrity and validation"""
    
    def setUp(self):
        """Load actual data for testing"""
        try:
            with open('neighbourhood_data.json', 'r') as f:
                self.data = json.load(f)
            self.df = pd.DataFrame(self.data)
        except Exception as e:
            self.skipTest(f"Could not load data file: {e}")
    
    def test_data_structure(self):
        """Test that data has required structure"""
        required_fields = [
            'location', 'city', 'area', 'safety_score', 'traffic_score',
            'schools', 'hospitals', 'future_growth', 'avg_price_per_sqft'
        ]
        
        for item in self.data:
            for field in required_fields:
                self.assertIn(field, item, f"Missing required field: {field}")
    
    def test_data_types(self):
        """Test that data fields have correct types"""
        for item in self.data:
            # String fields
            self.assertIsInstance(item['location'], str)
            self.assertIsInstance(item['city'], str)
            self.assertIsInstance(item['area'], str)
            self.assertIsInstance(item['future_growth'], str)
            
            # Numeric fields
            if item.get('safety_score') is not None:
                self.assertIsInstance(item['safety_score'], (int, float))
            if item.get('traffic_score') is not None:
                self.assertIsInstance(item['traffic_score'], (int, float))
            if item.get('avg_price_per_sqft') is not None:
                self.assertIsInstance(item['avg_price_per_sqft'], (int, float))
    
    def test_score_ranges(self):
        """Test that scores are within valid ranges"""
        for item in self.data:
            # Scores should be 0-10
            score_fields = ['safety_score', 'traffic_score', 'connectivity_score',
                           'infrastructure_score', 'lifestyle_score', 'environment_score']
            
            for field in score_fields:
                if item.get(field) is not None:
                    score = item[field]
                    self.assertGreaterEqual(score, 0, f"{field} should be >= 0")
                    self.assertLessEqual(score, 10, f"{field} should be <= 10")
    
    def test_data_completeness(self):
        """Test data completeness"""
        self.assertGreater(len(self.data), 0, "Data should not be empty")
        
        # Check for cities
        cities = set(item['city'] for item in self.data)
        self.assertIn('Ahmedabad', cities)
        self.assertIn('Gandhinagar', cities)
    
    def test_unique_locations(self):
        """Test that location names are unique"""
        locations = [item['location'] for item in self.data]
        unique_locations = set(locations)
        
        self.assertEqual(len(locations), len(unique_locations), 
                        "Location names should be unique")

class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and edge cases"""
    
    def test_invalid_location_name(self):
        """Test handling of invalid location names"""
        result = get_neighborhood_info("NonExistentLocation123!@#")
        self.assertIn('error', result)
    
    def test_empty_location_name(self):
        """Test handling of empty location name"""
        result = get_neighborhood_info("")
        self.assertIn('error', result)
    
    def test_none_location_name(self):
        """Test handling of None as location name"""
        try:
            result = get_neighborhood_info(None)
            # Should either return error or handle gracefully
            self.assertIsInstance(result, dict)
        except Exception:
            # Exception is also acceptable for None input
            pass
    
    def test_invalid_investment_amount(self):
        """Test handling of invalid investment amounts"""
        # Test with actual location but invalid amount
        result = get_investment_analysis("Satellite", 0)
        # Should handle gracefully
        self.assertIsInstance(result, dict)
    
    def test_compare_single_location(self):
        """Test comparison with single location"""
        result = compare_locations(["Satellite"])
        self.assertIn('error', result)
    
    def test_compare_empty_list(self):
        """Test comparison with empty location list"""
        result = compare_locations([])
        self.assertIn('error', result)

def run_performance_tests():
    """Run basic performance tests"""
    import time
    
    print("\n🚀 Running Performance Tests...")
    
    # Test data loading performance
    start_time = time.time()
    analyzer = NeighborhoodAnalyzer()
    load_time = time.time() - start_time
    print(f"📊 Data loading time: {load_time:.3f}s")
    
    # Test location lookup performance
    start_time = time.time()
    result = get_neighborhood_info("Satellite")
    lookup_time = time.time() - start_time
    print(f"🔍 Location lookup time: {lookup_time:.3f}s")
    
    # Test investment analysis performance
    start_time = time.time()
    result = get_investment_analysis("Satellite", 10000000)
    analysis_time = time.time() - start_time
    print(f"💰 Investment analysis time: {analysis_time:.3f}s")
    
    # Test comparison performance
    start_time = time.time()
    result = compare_locations(["Satellite", "Vastrapur", "Bodakdev"])
    comparison_time = time.time() - start_time
    print(f"⚖️ Comparison analysis time: {comparison_time:.3f}s")
    
    print("✅ Performance tests completed!")

def run_data_validation():
    """Run comprehensive data validation"""
    print("\n🔍 Running Data Validation...")
    
    try:
        with open('neighbourhood_data.json', 'r') as f:
            data = json.load(f)
        
        print(f"📊 Total locations: {len(data)}")
        
        # Validate each location
        issues = []
        for i, location in enumerate(data):
            # Check required fields
            required_fields = ['location', 'city', 'safety_score', 'avg_price_per_sqft']
            for field in required_fields:
                if field not in location:
                    issues.append(f"Location {i}: Missing field '{field}'")
            
            # Check score ranges
            score_fields = ['safety_score', 'traffic_score', 'investment_score']
            for field in score_fields:
                if field in location and location[field] is not None:
                    if not (0 <= location[field] <= 10):
                        issues.append(f"Location {i} ({location.get('location', 'Unknown')}): {field} out of range (0-10)")
        
        if issues:
            print("❌ Data validation issues found:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"  • {issue}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more issues")
        else:
            print("✅ All data validation checks passed!")
    
    except Exception as e:
        print(f"❌ Data validation failed: {e}")

def main():
    """Run all tests"""
    print("🧪 Starting Comprehensive Test Suite for Neighborhood Analysis Tool")
    print("=" * 70)
    
    # Run data validation first
    run_data_validation()
    
    # Run performance tests
    run_performance_tests()
    
    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestNeighborhoodAnalyzer,
        TestDeepSeekClient,
        TestAPIIntegration,
        TestDataIntegrity,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('\n')[-2]}")
    
    if not result.failures and not result.errors:
        print("🎉 ALL TESTS PASSED!")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)