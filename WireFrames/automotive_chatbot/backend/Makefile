# Makefile for Multi-Tenant SaaS Platform Testing
# Provides convenient commands for running tests and managing the test environment

.PHONY: help install test test-unit test-integration test-e2e test-security test-performance test-widget test-quick test-all test-ci clean setup-data cleanup-data lint format check coverage reports

# Default target
help:
	@echo "Multi-Tenant SaaS Platform Test Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install        Install all dependencies"
	@echo "  setup-data     Setup test data for ABC Motors and XYZ Auto"
	@echo "  cleanup-data   Cleanup all test data"
	@echo ""
	@echo "Test Commands:"
	@echo "  test           Run all tests (alias for test-all)"
	@echo "  test-unit      Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-e2e       Run end-to-end tests"
	@echo "  test-security  Run security tests"
	@echo "  test-performance Run performance tests"
	@echo "  test-widget    Run widget tests"
	@echo "  test-quick     Run quick tests (exclude slow)"
	@echo "  test-all       Run comprehensive test suite"
	@echo "  test-ci        Run tests in CI/CD mode"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint           Run code linting"
	@echo "  format         Format code"
	@echo "  check          Run linting and type checking"
	@echo "  coverage       Generate coverage report"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean          Clean up generated files"
	@echo "  reports        Open test reports in browser"
	@echo ""
	@echo "Examples:"
	@echo "  make test-unit coverage=true    # Run unit tests with coverage"
	@echo "  make test-quick                 # Run quick tests"
	@echo "  make test-all                   # Run all tests"

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-html pytest-json-report
	pip install pytest-xdist pytest-timeout pytest-mock
	pip install flake8 black isort bandit safety
	@echo "✅ Dependencies installed successfully"

# Test data management
setup-data:
	@echo "🔧 Setting up test data..."
	python run_tests.py --setup-data

cleanup-data:
	@echo "🧹 Cleaning up test data..."
	python run_tests.py --cleanup-data

# Individual test suites
test-unit:
	@echo "🧪 Running unit tests..."
	python run_tests.py --unit $(if $(coverage),--coverage,)

test-integration:
	@echo "🔗 Running integration tests..."
	python run_tests.py --integration $(if $(coverage),--coverage,)

test-e2e:
	@echo "🎭 Running end-to-end tests..."
	python run_tests.py --e2e

test-security:
	@echo "🔒 Running security tests..."
	python run_tests.py --security

test-performance:
	@echo "⚡ Running performance tests..."
	python run_tests.py --performance

test-widget:
	@echo "🎨 Running widget tests..."
	python run_tests.py --widget

test-quick:
	@echo "🚀 Running quick tests..."
	python run_tests.py --quick $(if $(coverage),--coverage,)

test-all:
	@echo "🎯 Running comprehensive test suite..."
	python run_tests.py --all $(if $(coverage),--coverage,)

test-ci:
	@echo "🤖 Running tests in CI/CD mode..."
	python run_tests.py --ci

# Alias for test-all
test: test-all

# Code quality
lint:
	@echo "🔍 Running code linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "✨ Formatting code..."
	black . --line-length 127
	isort . --profile black

check: lint
	@echo "✅ Code quality check completed"

coverage:
	@echo "📊 Generating coverage report..."
	python run_tests.py --unit --coverage
	@echo "📈 Coverage report generated in htmlcov/"

# Security scanning
security-scan:
	@echo "🔒 Running security scans..."
	bandit -r . -f txt
	safety check

# Utility commands
clean:
	@echo "🧹 Cleaning up generated files..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf test_reports/
	rm -rf .coverage
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup completed"

reports:
	@echo "📊 Opening test reports..."
	@if [ -d "test_reports" ]; then \
		echo "Available reports:"; \
		ls -la test_reports/; \
		echo "Opening latest HTML report..."; \
		if command -v xdg-open > /dev/null; then \
			xdg-open test_reports/$$(ls -t test_reports/*.html | head -1); \
		elif command -v open > /dev/null; then \
			open test_reports/$$(ls -t test_reports/*.html | head -1); \
		else \
			echo "Please open test_reports/ directory manually"; \
		fi; \
	else \
		echo "No test reports found. Run tests first."; \
	fi

# Development workflow
dev-setup: install setup-data
	@echo "🚀 Development environment setup completed"

dev-test: test-quick
	@echo "🔄 Quick development test completed"

dev-full: clean test-all
	@echo "🎯 Full development test cycle completed"

# CI/CD workflows
ci-quick: lint test-quick
	@echo "⚡ CI quick check completed"

ci-full: lint test-ci security-scan
	@echo "🤖 CI full pipeline completed"

# Parallel test execution
test-parallel:
	@echo "⚡ Running tests in parallel..."
	pytest -n auto tests/ -v

# Test specific clients
test-abc-motors:
	@echo "🚗 Running ABC Motors specific tests..."
	pytest tests/ -k "abc_motors" -v

test-xyz-auto:
	@echo "🚙 Running XYZ Auto specific tests..."
	pytest tests/ -k "xyz_auto" -v

# Database specific tests
test-database:
	@echo "🗄️ Running database specific tests..."
	pytest tests/ -m "database" -v

# API specific tests
test-api:
	@echo "🌐 Running API specific tests..."
	pytest tests/ -m "api" -v

# Authentication specific tests
test-auth:
	@echo "🔐 Running authentication specific tests..."
	pytest tests/ -m "auth" -v

# Slow tests only
test-slow:
	@echo "🐌 Running slow tests..."
	pytest tests/ -m "slow" -v

# Watch mode for development
test-watch:
	@echo "👀 Running tests in watch mode..."
	pytest-watch -- tests/ -v

# Generate test documentation
test-docs:
	@echo "📚 Generating test documentation..."
	pytest --collect-only --quiet tests/ > test_inventory.txt
	@echo "📋 Test inventory saved to test_inventory.txt"

# Performance profiling
test-profile:
	@echo "📈 Running performance profiling..."
	pytest tests/performance/ --profile -v

# Memory usage testing
test-memory:
	@echo "🧠 Running memory usage tests..."
	pytest tests/ --memray -v

# Test with different Python versions (if available)
test-python-versions:
	@echo "🐍 Testing with different Python versions..."
	@for version in 3.9 3.10 3.11; do \
		if command -v python$$version > /dev/null; then \
			echo "Testing with Python $$version..."; \
			python$$version -m pytest tests/unit/ -v; \
		fi; \
	done

# Stress testing
test-stress:
	@echo "💪 Running stress tests..."
	pytest tests/performance/ -v --stress

# Integration with external services
test-external:
	@echo "🌍 Running external service integration tests..."
	pytest tests/integration/ -m "external" -v

# Test data validation
test-data-validation:
	@echo "✅ Running test data validation..."
	python tests/data/setup_test_data.py --validate

# Backup test data
backup-test-data:
	@echo "💾 Backing up test data..."
	python tests/data/setup_test_data.py --backup

# Restore test data
restore-test-data:
	@echo "🔄 Restoring test data..."
	python tests/data/setup_test_data.py --restore

# Show test statistics
test-stats:
	@echo "📊 Generating test statistics..."
	pytest --collect-only tests/ | grep "<" | wc -l
	@echo "Total test functions found"

# Validate test environment
validate-env:
	@echo "🔍 Validating test environment..."
	@python -c "import sys; print(f'Python version: {sys.version}')"
	@python -c "import pytest; print(f'Pytest version: {pytest.__version__}')"
	@python -c "import pymongo; print(f'PyMongo version: {pymongo.__version__}')"
	@echo "✅ Test environment validation completed"

# Show help for specific test types
help-unit:
	@echo "Unit Tests Help"
	@echo "==============="
	@echo "Unit tests focus on testing individual components in isolation."
	@echo "They are fast, reliable, and should not depend on external services."
	@echo ""
	@echo "Commands:"
	@echo "  make test-unit           # Run all unit tests"
	@echo "  make test-unit coverage=true  # Run with coverage"

help-integration:
	@echo "Integration Tests Help"
	@echo "====================="
	@echo "Integration tests verify that different components work together correctly."
	@echo "They test database operations, API interactions, and client isolation."
	@echo ""
	@echo "Commands:"
	@echo "  make test-integration    # Run all integration tests"

help-e2e:
	@echo "End-to-End Tests Help"
	@echo "===================="
	@echo "E2E tests verify complete user workflows from start to finish."
	@echo "They test the entire application stack including UI interactions."
	@echo ""
	@echo "Commands:"
	@echo "  make test-e2e           # Run all E2E tests"

help-performance:
	@echo "Performance Tests Help"
	@echo "====================="
	@echo "Performance tests verify system behavior under load and stress conditions."
	@echo "They test response times, concurrent usage, and resource utilization."
	@echo ""
	@echo "Commands:"
	@echo "  make test-performance   # Run all performance tests"
	@echo "  make test-stress        # Run stress tests"

help-security:
	@echo "Security Tests Help"
	@echo "=================="
	@echo "Security tests verify data isolation, access control, and vulnerability protection."
	@echo "They test authentication, authorization, and data security measures."
	@echo ""
	@echo "Commands:"
	@echo "  make test-security      # Run all security tests"
	@echo "  make security-scan      # Run security vulnerability scans"