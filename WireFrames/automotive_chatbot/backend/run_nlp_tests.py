#!/usr/bin/env python3
"""
Simplified Natural Language Processing Tests Runner

This script runs the core NLP tests for RASA Actions without the full test suite
to avoid timeout issues and provide quick feedback.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def run_core_nlp_tests():
    """Run core NLP tests with simplified reporting"""
    print("🚀 Starting Core NLP Tests for RASA Actions...")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure reports directory exists
    reports_dir = Path('tests/reports')
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Test files to run
    test_files = [
        'tests/test_action_view_appointments.py',
        'tests/test_action_cancel_appointment.py',
        'tests/test_appointment_workflow.py',
        'tests/test_intent_validation_accuracy.py',
        'tests/test_multilingual_support.py'
    ]
    
    # Check which test files exist
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
            print(f"✅ Found test file: {test_file}")
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    if not existing_tests:
        print("❌ No test files found to run!")
        return False
    
    # Run tests with basic pytest options
    results = {}
    overall_success = True
    
    for test_file in existing_tests:
        print(f"\n🧪 Running {test_file}...")
        
        try:
            # Run individual test file with timeout
            cmd = [
                'python', '-m', 'pytest',
                test_file,
                '-v',
                '--tb=short',
                '--timeout=300',  # 5 minute timeout per test file
                '--disable-warnings'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=360,  # 6 minute overall timeout
                cwd=os.getcwd()
            )
            
            # Parse results
            success = result.returncode == 0
            results[test_file] = {
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout[-500:] if result.stdout else '',  # Last 500 chars
                'stderr': result.stderr[-300:] if result.stderr else ''   # Last 300 chars
            }
            
            if success:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED (return code: {result.returncode})")
                overall_success = False
                
                # Print error details
                if result.stderr:
                    print(f"   Error: {result.stderr[-200:]}")
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - TIMEOUT (exceeded 6 minutes)")
            results[test_file] = {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': 'Test execution timed out'
            }
            overall_success = False
        
        except Exception as e:
            print(f"💥 {test_file} - ERROR: {str(e)}")
            results[test_file] = {
                'success': False,
                'return_code': -2,
                'stdout': '',
                'stderr': str(e)
            }
            overall_success = False
    
    # Generate simple report
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_success': overall_success,
        'total_test_files': len(existing_tests),
        'passed_files': len([r for r in results.values() if r['success']]),
        'failed_files': len([r for r in results.values() if not r['success']]),
        'results': results
    }
    
    # Save report
    report_file = reports_dir / 'nlp_test_results.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"📁 Total test files: {report['total_test_files']}")
    print(f"✅ Passed files: {report['passed_files']}")
    print(f"❌ Failed files: {report['failed_files']}")
    print(f"📈 Success rate: {(report['passed_files']/report['total_test_files']*100):.1f}%")
    print(f"📄 Report saved to: {report_file}")
    
    if overall_success:
        print("\n🎉 All NLP tests completed successfully!")
    else:
        print("\n⚠️ Some tests failed. Check the report for details.")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_success

def check_test_environment():
    """Check if the test environment is properly set up"""
    print("🔍 Checking test environment...")
    
    # Check if we're in the right directory
    if not os.path.exists('tests'):
        print("❌ Tests directory not found. Make sure you're in the backend directory.")
        return False
    
    # Check if pytest is available
    try:
        result = subprocess.run(['python', '-m', 'pytest', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Pytest available: {result.stdout.strip()}")
        else:
            print("❌ Pytest not available")
            return False
    except Exception as e:
        print(f"❌ Error checking pytest: {e}")
        return False
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"✅ Python version: {python_version}")
    
    return True

def main():
    """Main function"""
    print("🤖 RASA Actions NLP Test Runner")
    print("=" * 50)
    
    # Check environment
    if not check_test_environment():
        print("❌ Environment check failed. Exiting.")
        return 1
    
    # Run tests
    success = run_core_nlp_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)