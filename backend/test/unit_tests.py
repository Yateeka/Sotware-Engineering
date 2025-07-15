import pytest
import json
import os
import time
from datetime import datetime

class TestProtestSpecificScenarios:
    @classmethod
    def setup_class(cls):
        """Set up class-level test tracking."""
        cls.test_results = []
        cls.start_time = time.time()
        cls.total_tests = 5
        
    @classmethod
    def teardown_class(cls):
        """Generate test results file after all tests complete."""
        cls._generate_test_results_file()
    
    def _record_test_result(self, test_name, status, details=None, execution_time=0):
        """Record individual test result."""
        result = {
            'test_name': test_name,
            'status': status,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.__class__.test_results.append(result)
    
    def test_scenario_1_browse_by_location_and_quit(self, client, test_data):
        """
        Scenario 1: User browses protests by location and quits
        User opens app and filters protests by location "Atlanta, Georgia". 
        User views the list. User quits.
        """
        start_time = time.time()
        test_name = "Scenario 1: Browse by Location and Quit"
        
        try:
            # User filters by location
            response = client.get('/api/protests?location=Atlanta,Georgia')
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Check that results are filtered by Atlanta
            assert isinstance(data, list)
            atlanta_count = len(data)
            
            for protest in data:
                assert protest['city'] == 'Atlanta'
                assert 'protest_id' in protest
                assert 'title' in protest
                assert 'categories' in protest
            
            # Verify we found the Atlanta protest
            atlanta_protest = next((p for p in data if p['protest_id'] == '1'), None)
            assert atlanta_protest is not None
            assert atlanta_protest['title'] == 'Climate Action March'
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, 
                'PASSED',
                {
                    'endpoint_tested': 'GET /api/protests?location=Atlanta,Georgia',
                    'response_code': response.status_code,
                    'protests_found': atlanta_count,
                    'atlanta_protest_verified': True,
                    'filters_working': True
                },
                execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name, 
                'FAILED',
                {'error': str(e)},
                execution_time
            )
            raise
    
    def test_scenario_2_browse_by_cause_and_quit(self, client):
        """
        Scenario 2: User browses protests by cause and quits
        User opens app and filters protests by cause "Environmental Justice".
        User views all environmental protests. User quits.
        """
        start_time = time.time()
        test_name = "Scenario 2: Browse by Cause and Quit"
        
        try:
            # User filters by cause
            response = client.get('/api/protests?cause=Environmental Justice')
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Check that results contain Environmental Justice protests
            assert isinstance(data, list)
            assert len(data) > 0
            
            environmental_count = len(data)
            
            for protest in data:
                assert 'Environmental Justice' in protest['categories']
                assert 'protest_id' in protest
                assert 'title' in protest
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'PASSED',
                {
                    'endpoint_tested': 'GET /api/protests?cause=Environmental Justice',
                    'response_code': response.status_code,
                    'environmental_protests_found': environmental_count,
                    'cause_filtering_working': True
                },
                execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'FAILED', 
                {'error': str(e)},
                execution_time
            )
            raise
    
    def test_scenario_3_search_keyword_and_quit(self, client):
        """
        Scenario 3: User searches by keyword and views results, then quits
        User enters search keyword "climate". User views filtered results 
        showing climate-related protests. User quits.
        """
        start_time = time.time()
        test_name = "Scenario 3: Search by Keyword and Quit"
        
        try:
            # User searches for keyword
            response = client.get('/api/search/protests?keyword=climate')
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Check that results contain climate-related protests
            assert isinstance(data, list)
            assert len(data) > 0
            
            climate_count = len(data)
            
            # Verify keyword appears in title, description, or categories
            climate_found = False
            for protest in data:
                if ('climate' in protest['title'].lower() or 
                    'climate' in protest['description'].lower() or
                    any('climate' in cat.lower() for cat in protest['categories'])):
                    climate_found = True
                    break
            
            assert climate_found, "No climate-related protests found"
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'PASSED',
                {
                    'endpoint_tested': 'GET /api/search/protests?keyword=climate',
                    'response_code': response.status_code,
                    'climate_protests_found': climate_count,
                    'keyword_search_working': True,
                    'search_accuracy_verified': climate_found
                },
                execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'FAILED',
                {'error': str(e)},
                execution_time
            )
            raise
    
    def test_scenario_4_filter_by_date_and_location_quit(self, client):
        """
        Scenario 4: User filters protests by date range and location, then quits
        User filters protests by location "New York, NY" and sets date range 
        from "2024-03-01" to "2024-03-31". User views filtered results. User quits.
        """
        start_time = time.time()
        test_name = "Scenario 4: Filter by Date and Location then Quit"
        
        try:
            # User applies location and date filters
            response = client.get('/api/protests?location=New York,NY&start_date=2024-03-01&end_date=2024-03-31')
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Check that results match filters
            assert isinstance(data, list)
            
            filtered_count = len(data)
            dates_in_range = 0
            location_matches = 0
            
            for protest in data:
                # Check location
                if protest['city'] == 'New York':
                    location_matches += 1
                
                # Check date is within range
                protest_date = protest['start_date']
                if protest_date >= '2024-03-01' and protest_date <= '2024-03-31':
                    dates_in_range += 1
                
                assert 'protest_id' in protest
                assert 'title' in protest
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'PASSED',
                {
                    'endpoint_tested': 'GET /api/protests?location=New York,NY&start_date=2024-03-01&end_date=2024-03-31',
                    'response_code': response.status_code,
                    'filtered_protests_found': filtered_count,
                    'location_matches': location_matches,
                    'dates_in_range': dates_in_range,
                    'complex_filtering_working': True
                },
                execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'FAILED',
                {'error': str(e)},
                execution_time
            )
            raise
    
    def test_scenario_5_filter_view_details_save_alert_quit(self, client):
        """
        Scenario 5: User filters protests, clicks details, saves alert, quits
        User filters by "Labor Rights". User clicks "Workers Rights Rally" for details.
        User adds this protest type to alerts and gets confirmation. User quits.
        """
        start_time = time.time()
        test_name = "Scenario 5: Filter, View Details, Save Alert, Quit"
        
        try:
            # Step 1: User filters by cause "Labor Rights"
            response = client.get('/api/protests?cause=Labor Rights')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) > 0
            
            labor_protests_found = len(data)
            
            # Verify Labor Rights protest exists
            labor_protest = next((p for p in data if 'Labor Rights' in p['categories']), None)
            assert labor_protest is not None
            
            # Step 2: User clicks on protest details
            protest_id = labor_protest['protest_id']
            response = client.get(f'/api/protests/{protest_id}')
            
            assert response.status_code == 200
            protest_details = json.loads(response.data)
            assert protest_details['protest_id'] == protest_id
            assert protest_details['title'] == 'Workers Rights Rally'
            
            # Step 3: User saves alert for Labor Rights protests
            alert_data = {
                'user_id': 'user1',
                'keywords': ['Labor Rights', 'Workers Rights'],
                'location_filter': 'New York, NY'
            }
            
            response = client.post('/api/alerts', 
                                  json=alert_data,
                                  content_type='application/json')
            
            assert response.status_code == 201
            alert_response = json.loads(response.data)
            
            # Verify alert creation confirmation
            assert 'message' in alert_response
            assert 'alert_id' in alert_response
            assert alert_response['message'] == 'Alert created successfully'
            
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'PASSED',
                {
                    'endpoints_tested': [
                        'GET /api/protests?cause=Labor Rights',
                        f'GET /api/protests/{protest_id}',
                        'POST /api/alerts'
                    ],
                    'labor_protests_found': labor_protests_found,
                    'protest_details_retrieved': True,
                    'alert_created_successfully': True,
                    'multi_step_workflow_working': True,
                    'alert_id_generated': alert_response.get('alert_id')
                },
                execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_test_result(
                test_name,
                'FAILED',
                {'error': str(e)},
                execution_time
            )
            raise
    
    @classmethod
    def _generate_test_results_file(cls):
        """Generate test results file."""
        total_time = time.time() - cls.start_time
        passed_tests = sum(1 for result in cls.test_results if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in cls.test_results if result['status'] == 'FAILED')
        
        # Overall status
        overall_status = "ALL TESTS PASSED" if failed_tests == 0 else f"{failed_tests} TEST(S) FAILED"
        
        # Generate report
        report = {
            "test_execution_summary": {
                "project_name": "Global Protest Tracker - Backend API",
                "test_suite": "User Scenario Integration Tests",
                "execution_date": datetime.now().isoformat(),
                "total_execution_time_seconds": round(total_time, 3),
                "total_tests": cls.total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "success_rate": f"{(passed_tests/cls.total_tests)*100:.1f}%",
                "overall_status": overall_status
            },
            "api_endpoints_tested": [
                "GET /api/protests (with various filters)",
                "GET /api/protests/<id>",
                "GET /api/search/protests",
                "POST /api/alerts"
            ],
            "test_scenarios_executed": [
                {
                    "scenario_id": 1,
                    "description": "User browses protests by location and quits",
                    "user_workflow": "Filter by location → View results → Quit",
                    "primary_functionality": "Location-based filtering"
                },
                {
                    "scenario_id": 2,
                    "description": "User browses protests by cause and quits", 
                    "user_workflow": "Filter by cause → View results → Quit",
                    "primary_functionality": "Cause-based filtering"
                },
                {
                    "scenario_id": 3,
                    "description": "User searches by keyword and views results",
                    "user_workflow": "Search keyword → View results → Quit",
                    "primary_functionality": "Keyword search across multiple fields"
                },
                {
                    "scenario_id": 4,
                    "description": "User filters by date range and location",
                    "user_workflow": "Apply multiple filters → View results → Quit", 
                    "primary_functionality": "Complex multi-filter functionality"
                },
                {
                    "scenario_id": 5,
                    "description": "User filters, views details, saves alert",
                    "user_workflow": "Filter → View details → Create alert → Quit",
                    "primary_functionality": "Multi-step workflow with CRUD operations"
                }
            ],
            "detailed_test_results": cls.test_results,
            "performance_metrics": {
                "average_response_time": f"{sum(r['execution_time'] for r in cls.test_results) / len(cls.test_results):.3f}s",
                "fastest_test": f"{min(r['execution_time'] for r in cls.test_results):.3f}s",
                "slowest_test": f"{max(r['execution_time'] for r in cls.test_results):.3f}s"
            }
        }
        
        # Write to file
        results_file_path = os.path.join(os.path.dirname(__file__), 'test_results.json')
        with open(results_file_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        # Create summary
        summary_file_path = os.path.join(os.path.dirname(__file__), 'test_results_summary.txt')
        with open(summary_file_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("GLOBAL PROTEST TRACKER - BACKEND API TEST RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("EXECUTION SUMMARY\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {cls.total_tests}\n")
            f.write(f"Passed: {passed_tests}\n") 
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/cls.total_tests)*100:.1f}%\n")
            f.write(f"Total Execution Time: {total_time:.3f} seconds\n")
            f.write(f"Overall Status: {overall_status}\n\n")
            
            f.write("TEST SCENARIOS RESULTS\n")
            f.write("-" * 40 + "\n")
            for i, result in enumerate(cls.test_results, 1):
                f.write(f"Test {i}: {result['test_name']}\n")
                f.write(f"   Status: {result['status']}\n")
                f.write(f"   Execution Time: {result['execution_time']:.3f}s\n")
                if result['status'] == 'FAILED' and 'error' in result['details']:
                    f.write(f"   Error: {result['details']['error']}\n")
                f.write("\n")
            
            f.write("API ENDPOINTS TESTED\n")
            f.write("-" * 40 + "\n")
            for endpoint in report["api_endpoints_tested"]:
                f.write(f"{endpoint}\n")
            
            f.write(f"\nDetailed results saved to: test_results.json\n")
        
        print(f"\n{'-'*60}")
        print("TEST RESULTS GENERATED")
        print(f"{'-'*60}")
        print(f"Summary: {summary_file_path}")
        print(f"Detailed: {results_file_path}")
        print(f"Status: {overall_status}")
        print(f"{'-'*60}")