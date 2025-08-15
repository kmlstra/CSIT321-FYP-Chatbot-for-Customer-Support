# Multi-Tenant SaaS Platform - Comprehensive Test Suite

This directory contains a comprehensive test suite for the multi-tenant SaaS platform, designed to ensure robust functionality, security, and performance across all components.

## 📁 Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── pytest.ini                 # Pytest settings and markers
├── README.md                   # This documentation
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_auth.py           # Authentication endpoint tests
│   ├── test_client_management.py  # Client management tests
│   └── test_widget_api.py     # Widget API tests
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_database_operations.py  # Database and isolation tests
│   └── test_api_endpoints.py  # API integration tests
├── e2e/                       # End-to-end tests
│   ├── __init__.py
│   └── test_complete_workflows.py  # Complete user workflows
├── security/                  # Security tests
│   ├── __init__.py
│   └── test_security.py       # Security and access control tests
├── performance/               # Performance tests
│   ├── __init__.py
│   └── test_performance.py    # Load and stress tests
├── widget/                    # Widget-specific tests
│   ├── __init__.py
│   └── test_widget_functionality.py  # Widget feature tests
└── data/                      # Test data management
    ├── __init__.py
    ├── setup_test_data.py     # Test data setup scripts
    └── cleanup_test_data.py   # Test data cleanup scripts
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **MongoDB** running (local or remote)
3. **Node.js 18+** for frontend components
4. **Required Python packages** (see Installation)

### Installation

```bash
# Install Python dependencies
pip install -r ../requirements.txt

# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-json-report
pip install pytest-xdist pytest-timeout pytest-mock

# Or use the Makefile
make install
```

### Environment Setup

1. **Copy environment template:**
```bash
cp .env.example .env.test
```

2. **Configure test environment variables:**
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/test_automotive_platform
TEST_DB_NAME=test_automotive_platform

# Authentication
JWT_SECRET=test_jwt_secret_key_for_testing_only

# API
API_BASE_URL=http://localhost:8000

# RASA (optional for mocked tests)
RASA_SERVER_URL=http://localhost:5005
RASA_MOCK_RESPONSES=true

# Test Configuration
ENVIRONMENT=test
DEBUG=false
VERBOSE=false
```

### Running Tests

#### Using the Test Runner (Recommended)

```bash
# Run all tests
python ../run_tests.py --all

# Run specific test suites
python ../run_tests.py --unit
python ../run_tests.py --integration
python ../run_tests.py --e2e
python ../run_tests.py --security
python ../run_tests.py --performance
python ../run_tests.py --widget

# Run quick tests (exclude slow tests)
python ../run_tests.py --quick

# Run with coverage
python ../run_tests.py --unit --coverage

# CI/CD mode
python ../run_tests.py --ci
```

#### Using Makefile

```bash
# Run all tests
make test

# Run specific test suites
make test-unit
make test-integration
make test-e2e
make test-security
make test-performance
make test-widget

# Run with coverage
make test-unit coverage=true

# Quick development tests
make test-quick

# CI pipeline
make ci-full
```

#### Using Pytest Directly

```bash
# Run all tests
pytest -v

# Run specific test files
pytest tests/unit/test_auth.py -v

# Run tests with markers
pytest -m "unit" -v
pytest -m "integration and not slow" -v

# Run tests with coverage
pytest --cov=backend --cov-report=html -v

# Run tests in parallel
pytest -n auto -v
```

## 🧪 Test Categories

### Unit Tests
**Location:** `tests/unit/`
**Purpose:** Test individual components in isolation
**Markers:** `@pytest.mark.unit`

- **Authentication Tests** (`test_auth.py`)
  - Client login/logout
  - Super admin authentication
  - Token validation
  - Password security
  - Rate limiting

- **Client Management Tests** (`test_client_management.py`)
  - Client registration
  - Client approval workflow
  - Client settings management
  - Data validation

- **Widget API Tests** (`test_widget_api.py`)
  - Widget configuration
  - Embed script generation
  - Chat functionality
  - Customization options

### Integration Tests
**Location:** `tests/integration/`
**Purpose:** Test component interactions and database operations
**Markers:** `@pytest.mark.integration`

- **Database Operations** (`test_database_operations.py`)
  - Client data isolation
  - Cross-client access prevention
  - Transaction integrity
  - Index performance

- **API Endpoints** (`test_api_endpoints.py`)
  - End-to-end API workflows
  - Authentication integration
  - Data consistency
  - Error handling

### End-to-End Tests
**Location:** `tests/e2e/`
**Purpose:** Test complete user workflows
**Markers:** `@pytest.mark.e2e`

- **Complete Workflows** (`test_complete_workflows.py`)
  - Client onboarding process
  - Widget deployment and usage
  - Appointment booking flow
  - Multi-client scenarios

### Security Tests
**Location:** `tests/security/`
**Purpose:** Verify security measures and access controls
**Markers:** `@pytest.mark.security`

- **Security Tests** (`test_security.py`)
  - Authentication security
  - Authorization controls
  - Data isolation
  - Injection prevention
  - XSS protection

### Performance Tests
**Location:** `tests/performance/`
**Purpose:** Test system performance under load
**Markers:** `@pytest.mark.performance`

- **Performance Tests** (`test_performance.py`)
  - Concurrent user handling
  - Load testing
  - Response time analysis
  - Memory usage
  - Database performance

### Widget Tests
**Location:** `tests/widget/`
**Purpose:** Test widget-specific functionality
**Markers:** `@pytest.mark.widget`

- **Widget Functionality** (`test_widget_functionality.py`)
  - Client-specific configurations
  - Branding customization
  - Feature toggles
  - Responsive design
  - Analytics integration

## 🔧 Test Configuration

### Pytest Markers

The test suite uses the following markers to categorize tests:

```python
# Test type markers
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.security      # Security tests
@pytest.mark.performance   # Performance tests
@pytest.mark.widget        # Widget tests

# Special markers
@pytest.mark.slow          # Tests taking >5 seconds
@pytest.mark.auth          # Authentication tests
@pytest.mark.database      # Database tests
@pytest.mark.api           # API tests

# Client-specific markers
@pytest.mark.abc_motors    # ABC Motors specific tests
@pytest.mark.xyz_auto      # XYZ Auto specific tests

# Environment markers
@pytest.mark.external      # Requires external services
@pytest.mark.stress        # Stress testing
```

### Running Specific Test Categories

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run authentication tests
pytest -m "auth" -v

# Run database tests
pytest -m "database" -v

# Run client-specific tests
pytest -m "abc_motors" -v
pytest -m "xyz_auto" -v

# Combine markers
pytest -m "unit and not slow" -v
pytest -m "(integration or e2e) and not external" -v
```

## 📊 Test Data Management

### Test Clients

The test suite includes predefined test clients:

1. **ABC Motors** (`abc_motors`)
   - Premium subscription
   - Full feature set
   - Automotive dealership

2. **XYZ Auto Services** (`xyz_auto`)
   - Standard subscription
   - Limited features
   - Automotive service center

3. **Test Client Basic** (`test_client_basic`)
   - Basic subscription
   - Minimal features
   - General testing

### Data Setup and Cleanup

```bash
# Setup test data
python ../run_tests.py --setup-data

# Cleanup test data
python ../run_tests.py --cleanup-data

# Using Makefile
make setup-data
make cleanup-data
```

### Custom Test Data

To create custom test data:

```python
from tests.data.setup_test_data import create_test_client

# Create a custom test client
client_data = {
    "business_name": "Custom Auto Shop",
    "domain": "customauto.com",
    "email": "admin@customauto.com",
    "subscription_plan": "premium"
}

client_id = create_test_client(client_data)
```

## 📈 Coverage and Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# Generate terminal coverage report
pytest --cov=backend --cov-report=term-missing

# Generate XML coverage report (for CI)
pytest --cov=backend --cov-report=xml
```

### Test Reports

The test runner generates comprehensive reports:

- **HTML Reports:** `test_reports/*.html`
- **JSON Reports:** `test_reports/*.json`
- **Coverage Reports:** `htmlcov/index.html`
- **Summary Reports:** `test_reports/test_summary_*.json`

### Viewing Reports

```bash
# Open latest test report
make reports

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🔄 Continuous Integration

### GitHub Actions

The repository includes a comprehensive CI/CD pipeline (`.github/workflows/test.yml`):

- **Matrix Testing:** Python 3.9, 3.10, 3.11 × Node.js 18, 20
- **Services:** MongoDB, Redis (if needed)
- **Test Stages:**
  1. Linting and code quality
  2. Quick tests
  3. Unit tests with coverage
  4. Integration tests
  5. Security tests
  6. E2E tests (on main branch)
  7. Performance tests (on main branch)

### Local CI Simulation

```bash
# Run CI pipeline locally
python ../run_tests.py --ci

# Or using Makefile
make ci-full
```

## 🛠️ Development Workflow

### Pre-commit Testing

```bash
# Quick development tests
make dev-test

# Full development cycle
make dev-full
```

### Test-Driven Development

1. **Write failing test:**
```python
def test_new_feature():
    # Test the new feature
    assert new_feature() == expected_result
```

2. **Run the test (should fail):**
```bash
pytest tests/unit/test_new_feature.py::test_new_feature -v
```

3. **Implement the feature**

4. **Run the test again (should pass):**
```bash
pytest tests/unit/test_new_feature.py::test_new_feature -v
```

5. **Run full test suite:**
```bash
make test-quick
```

### Debugging Tests

```bash
# Run with verbose output
pytest -v -s

# Run with debugging
pytest --pdb

# Run specific test with debugging
pytest tests/unit/test_auth.py::test_client_login --pdb -s

# Run with print statements
pytest -v -s --capture=no
```

## 📋 Best Practices

### Writing Tests

1. **Follow the AAA pattern:**
   - **Arrange:** Set up test data
   - **Act:** Execute the function
   - **Assert:** Verify the result

2. **Use descriptive test names:**
```python
def test_client_login_with_valid_credentials_returns_access_token():
    pass

def test_client_login_with_invalid_password_returns_401():
    pass
```

3. **Use fixtures for common setup:**
```python
@pytest.fixture
def authenticated_client():
    # Setup authenticated client
    return client

def test_protected_endpoint(authenticated_client):
    # Use the fixture
    response = authenticated_client.get("/protected")
    assert response.status_code == 200
```

4. **Test edge cases:**
   - Empty inputs
   - Invalid data types
   - Boundary conditions
   - Error scenarios

5. **Keep tests independent:**
   - Each test should be able to run in isolation
   - Use proper setup and teardown
   - Don't rely on test execution order

### Performance Considerations

1. **Use appropriate markers:**
```python
@pytest.mark.slow
def test_large_dataset_processing():
    pass
```

2. **Mock external services:**
```python
@pytest.mark.unit
def test_api_call_with_mocked_service(mock_external_api):
    pass
```

3. **Use parallel execution for independent tests:**
```bash
pytest -n auto
```

### Security Testing

1. **Test authentication and authorization:**
   - Valid and invalid credentials
   - Token expiration
   - Role-based access

2. **Test input validation:**
   - SQL injection attempts
   - XSS payloads
   - Invalid data formats

3. **Test data isolation:**
   - Cross-client access prevention
   - Proper data filtering
   - Secure API endpoints

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors:**
```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Verify connection string
echo $MONGODB_URI
```

2. **Import Errors:**
```bash
# Ensure Python path is correct
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install missing dependencies
pip install -r requirements.txt
```

3. **Test Data Issues:**
```bash
# Clean and recreate test data
make cleanup-data
make setup-data
```

4. **Port Conflicts:**
```bash
# Check if ports are in use
netstat -an | grep :8000
netstat -an | grep :27017
```

### Debug Mode

```bash
# Run tests with debug output
DEBUG=true pytest -v -s

# Run with verbose logging
VERBOSE=true pytest -v
```

### Getting Help

1. **Check test logs:**
   - Test reports in `test_reports/`
   - Coverage reports in `htmlcov/`

2. **Run configuration validation:**
```bash
python ../test_config.py
```

3. **Verify environment:**
```bash
make validate-env
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [MongoDB Testing Best Practices](https://docs.mongodb.com/manual/tutorial/test-with-mongodb/)
- [Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## 🤝 Contributing

When adding new tests:

1. **Follow the existing structure**
2. **Add appropriate markers**
3. **Include documentation**
4. **Update this README if needed**
5. **Ensure tests pass in CI**

### Test Checklist

- [ ] Test follows AAA pattern
- [ ] Descriptive test name
- [ ] Appropriate markers added
- [ ] Edge cases covered
- [ ] Proper cleanup
- [ ] Documentation updated
- [ ] CI tests pass

---

**Happy Testing! 🧪✨**