#!/usr/bin/env python3
"""
Comprehensive Test Runner for Multi-Tenant SaaS Platform

This script provides various test execution options:
- Run all tests
- Run specific test suites (unit, integration, e2e, security, performance, widget)
- Run tests with different configurations
- Generate comprehensive reports
- Setup and cleanup test data

Usage:
    python run_tests.py --all                    # Run all tests
    python run_tests.py --unit                   # Run only unit tests
    python run_tests.py --integration            # Run only integration tests
    python run_tests.py --e2e                    # Run only end-to-end tests
    python run_tests.py --security               # Run only security tests
    python run_tests.py --performance            # Run only performance tests
    python run_tests.py --widget                 # Run only widget tests
    python run_tests.py --quick                  # Run quick tests (exclude slow)
    python run_tests.py --coverage               # Run with coverage report
    python run_tests.py --setup-data             # Setup test data only
    python run_tests.py --cleanup-data           # Cleanup test data only
    python run_tests.py --ci                     # CI/CD mode (no interactive)
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

class TestRunner:
    """Comprehensive test runner for the multi-tenant SaaS platform."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.test_dir = self.backend_dir / "tests"
        self.reports_dir = self.backend_dir / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test suite configurations
        self.test_suites = {
            'unit': {
                'path': 'tests/unit',
                'markers': 'unit',
                'description': 'Unit tests for individual components'
            },
            'integration': {
                'path': 'tests/integration',
                'markers': 'integration',
                'description': 'Integration tests for database and API interactions'
            },
            'e2e': {
                'path': 'tests/e2e',
                'markers': 'e2e',
                'description': 'End-to-end tests for complete workflows'
            },
            'security': {
                'path': 'tests/security',
                'markers': 'security',
                'description': 'Security tests for data isolation and access control'
            },
            'performance': {
                'path': 'tests/performance',
                'markers': 'performance',
                'description': 'Performance tests for concurrent usage and load testing'
            },
            'widget': {
                'path': 'tests/widget',
                'markers': 'widget',
                'description': 'Widget functionality tests with different client configurations'
            }
        }
    
    def setup_test_data(self) -> bool:
        """Setup test data for ABC Motors and XYZ Auto."""
        print("\n🔧 Setting up test data...")
        try:
            from tests.data.setup_test_data import setup_all_test_data
            setup_all_test_data()
            print("✅ Test data setup completed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to setup test data: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Cleanup test data."""
        print("\n🧹 Cleaning up test data...")
        try:
            from tests.data.cleanup_test_data import cleanup_all_test_data
            cleanup_all_test_data()
            print("✅ Test data cleanup completed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to cleanup test data: {e}")
            return False
    
    def run_pytest(self, args: List[str], suite_name: str = "tests") -> tuple[bool, str]:
        """Run pytest with given arguments."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"{suite_name}_{timestamp}.html"
        json_report_file = self.reports_dir / f"{suite_name}_{timestamp}.json"
        
        # Base pytest command
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "--tb=short",
            f"--html={report_file}",
            "--self-contained-html",
            f"--json-report={json_report_file}"
        ] + args
        
        print(f"\n🚀 Running {suite_name} tests...")
        print(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Print results
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            success = result.returncode == 0
            
            print(f"\n{'✅' if success else '❌'} {suite_name} tests {'passed' if success else 'failed'}")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"📊 HTML Report: {report_file}")
            print(f"📋 JSON Report: {json_report_file}")
            
            return success, str(report_file)
            
        except subprocess.TimeoutExpired:
            print(f"❌ {suite_name} tests timed out after 30 minutes")
            return False, ""
        except Exception as e:
            print(f"❌ Error running {suite_name} tests: {e}")
            return False, ""
    
    def run_unit_tests(self, coverage: bool = False) -> tuple[bool, str]:
        """Run unit tests."""
        args = ["-m", "unit", "tests/unit"]
        if coverage:
            args.extend(["--cov=backend", "--cov-report=html", "--cov-report=term-missing"])
        return self.run_pytest(args, "unit")
    
    def run_integration_tests(self, coverage: bool = False) -> tuple[bool, str]:
        """Run integration tests."""
        args = ["-m", "integration", "tests/integration"]
        if coverage:
            args.extend(["--cov=backend", "--cov-report=html", "--cov-report=term-missing"])
        return self.run_pytest(args, "integration")
    
    def run_e2e_tests(self) -> tuple[bool, str]:
        """Run end-to-end tests."""
        args = ["-m", "e2e", "tests/e2e"]
        return self.run_pytest(args, "e2e")
    
    def run_security_tests(self) -> tuple[bool, str]:
        """Run security tests."""
        args = ["-m", "security", "tests/security"]
        return self.run_pytest(args, "security")
    
    def run_performance_tests(self) -> tuple[bool, str]:
        """Run performance tests."""
        args = ["-m", "performance", "tests/performance"]
        return self.run_pytest(args, "performance")
    
    def run_widget_tests(self) -> tuple[bool, str]:
        """Run widget tests."""
        args = ["-m", "widget", "tests/widget"]
        return self.run_pytest(args, "widget")
    
    def run_quick_tests(self, coverage: bool = False) -> tuple[bool, str]:
        """Run quick tests (exclude slow tests)."""
        args = ["-m", "not slow", "tests/"]
        if coverage:
            args.extend(["--cov=backend", "--cov-report=html", "--cov-report=term-missing"])
        return self.run_pytest(args, "quick")
    
    def run_all_tests(self, coverage: bool = False) -> tuple[bool, List[str]]:
        """Run all test suites."""
        print("\n🎯 Running comprehensive test suite...")
        
        # Setup test data first
        if not self.setup_test_data():
            return False, []
        
        results = []
        reports = []
        
        try:
            # Run each test suite
            test_methods = [
                ("Unit", self.run_unit_tests),
                ("Integration", self.run_integration_tests),
                ("End-to-End", self.run_e2e_tests),
                ("Security", self.run_security_tests),
                ("Performance", self.run_performance_tests),
                ("Widget", self.run_widget_tests)
            ]
            
            for suite_name, test_method in test_methods:
                print(f"\n{'='*60}")
                print(f"Running {suite_name} Tests")
                print(f"{'='*60}")
                
                if suite_name in ["Unit", "Integration"] and coverage:
                    success, report = test_method(coverage=True)
                else:
                    success, report = test_method()
                
                results.append(success)
                if report:
                    reports.append(report)
                
                if not success:
                    print(f"⚠️  {suite_name} tests failed, but continuing with other suites...")
        
        finally:
            # Cleanup test data
            self.cleanup_test_data()
        
        # Generate summary report
        self.generate_summary_report(results, reports)
        
        all_passed = all(results)
        return all_passed, reports
    
    def generate_summary_report(self, results: List[bool], reports: List[str]):
        """Generate a summary report of all test results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.reports_dir / f"test_summary_{timestamp}.json"
        
        suite_names = ["Unit", "Integration", "End-to-End", "Security", "Performance", "Widget"]
        
        summary = {
            "timestamp": timestamp,
            "total_suites": len(results),
            "passed_suites": sum(results),
            "failed_suites": len(results) - sum(results),
            "success_rate": (sum(results) / len(results)) * 100 if results else 0,
            "suite_results": {
                suite_names[i]: "PASSED" if results[i] else "FAILED"
                for i in range(len(results))
            },
            "reports": reports
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Passed: {summary['passed_suites']}")
        print(f"Failed: {summary['failed_suites']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"\nDetailed Results:")
        for suite, result in summary['suite_results'].items():
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"  {status_icon} {suite}: {result}")
        print(f"\n📊 Summary Report: {summary_file}")
    
    def run_ci_tests(self) -> bool:
        """Run tests in CI/CD mode."""
        print("\n🤖 Running tests in CI/CD mode...")
        
        # Run quick tests first
        print("\n1️⃣ Running quick tests...")
        quick_success, _ = self.run_quick_tests(coverage=True)
        
        if not quick_success:
            print("❌ Quick tests failed, stopping CI run")
            return False
        
        # Run all tests
        print("\n2️⃣ Running full test suite...")
        all_success, _ = self.run_all_tests(coverage=True)
        
        return all_success

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for Multi-Tenant SaaS Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --unit --coverage        # Run unit tests with coverage
  python run_tests.py --quick                  # Run quick tests only
  python run_tests.py --ci                     # CI/CD mode
  python run_tests.py --setup-data             # Setup test data only
        """
    )
    
    # Test suite options
    parser.add_argument('--all', action='store_true', help='Run all test suites')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests')
    parser.add_argument('--security', action='store_true', help='Run security tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--widget', action='store_true', help='Run widget tests')
    parser.add_argument('--quick', action='store_true', help='Run quick tests (exclude slow)')
    
    # Configuration options
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--ci', action='store_true', help='Run in CI/CD mode')
    
    # Data management options
    parser.add_argument('--setup-data', action='store_true', help='Setup test data only')
    parser.add_argument('--cleanup-data', action='store_true', help='Cleanup test data only')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    runner = TestRunner()
    
    try:
        # Data management operations
        if args.setup_data:
            success = runner.setup_test_data()
            sys.exit(0 if success else 1)
        
        if args.cleanup_data:
            success = runner.cleanup_test_data()
            sys.exit(0 if success else 1)
        
        # CI/CD mode
        if args.ci:
            success = runner.run_ci_tests()
            sys.exit(0 if success else 1)
        
        # Individual test suites
        if args.all:
            success, _ = runner.run_all_tests(coverage=args.coverage)
            sys.exit(0 if success else 1)
        
        if args.unit:
            success, _ = runner.run_unit_tests(coverage=args.coverage)
            sys.exit(0 if success else 1)
        
        if args.integration:
            success, _ = runner.run_integration_tests(coverage=args.coverage)
            sys.exit(0 if success else 1)
        
        if args.e2e:
            success, _ = runner.run_e2e_tests()
            sys.exit(0 if success else 1)
        
        if args.security:
            success, _ = runner.run_security_tests()
            sys.exit(0 if success else 1)
        
        if args.performance:
            success, _ = runner.run_performance_tests()
            sys.exit(0 if success else 1)
        
        if args.widget:
            success, _ = runner.run_widget_tests()
            sys.exit(0 if success else 1)
        
        if args.quick:
            success, _ = runner.run_quick_tests(coverage=args.coverage)
            sys.exit(0 if success else 1)
        
        # If no specific test suite selected, show help
        parser.print_help()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()