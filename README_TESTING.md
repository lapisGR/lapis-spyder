# Testing Guide for Lapis Spider

This guide explains how to run tests for the Lapis Spider project.

## Quick Start

Run all tests with a single command:

```bash
./run_tests.sh
```

## Manual Testing Setup

### 1. Install Test Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install test packages
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 2. Set Test Environment Variables

```bash
export APP_ENV=test
export DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_lapis_spider
export MONGODB_URI=mongodb://localhost:27017
export MONGODB_DATABASE=test_lapis_spider
export REDIS_URL=redis://localhost:6379/1
export JWT_SECRET_KEY=test_secret_key
export GOOGLE_API_KEY=test_api_key
```

### 3. Run Tests

#### Run All Tests
```bash
pytest tests/ -v
```

#### Run with Coverage
```bash
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

#### Run Specific Test Files
```bash
# Test authentication
pytest tests/test_auth.py -v

# Test crawler
pytest tests/test_crawler.py -v

# Test AI integration
pytest tests/test_ai.py -v

# Test API endpoints
pytest tests/test_api.py -v

# Test utilities
pytest tests/test_utils.py -v
```

#### Run Tests by Category
```bash
# Run only unit tests (fast)
pytest tests/ -v -m "not integration"

# Run only integration tests (slower)
pytest tests/ -v -m "integration"

# Run tests in parallel
pytest tests/ -v -n 4
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py         # Shared fixtures
├── test_auth.py        # Authentication tests
├── test_crawler.py     # Crawler functionality tests
├── test_ai.py          # AI integration tests
├── test_api.py         # API endpoint tests
└── test_utils.py       # Utility function tests
```

## Test Categories

### 1. Unit Tests
- Fast, isolated tests
- Mock external dependencies
- Test individual functions/classes

### 2. Integration Tests
- Test component interactions
- May use test databases
- Slower but more comprehensive

### 3. API Tests
- Test HTTP endpoints
- Verify request/response format
- Check authentication/authorization

## Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Test suite for my feature."""
    
    @pytest.fixture
    def setup(self):
        """Setup test data."""
        return {"test": "data"}
    
    def test_basic_functionality(self, setup):
        """Test basic feature behavior."""
        result = my_function(setup)
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async feature."""
        result = await my_async_function()
        assert result is not None
    
    @patch('src.module.external_service')
    def test_with_mock(self, mock_service):
        """Test with mocked dependency."""
        mock_service.return_value = "mocked"
        result = function_using_service()
        assert result == "mocked"
```

## Debugging Tests

### Run with Debugging Output
```bash
# Show print statements
pytest tests/ -v -s

# Show full traceback
pytest tests/ -v --tb=long

# Drop into debugger on failure
pytest tests/ -v --pdb

# Run specific test
pytest tests/test_auth.py::TestAuthAPI::test_login_success -v
```

### Check Test Coverage

After running tests with coverage:

1. **Terminal Report**: See missing lines in terminal output
2. **HTML Report**: Open `htmlcov/index.html` in browser
3. **Coverage Goals**:
   - Overall: >80%
   - Critical paths: >90%
   - New code: 100%

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      mongodb:
        image: mongo:6
        options: >-
          --health-cmd "mongosh --eval 'quit(db.runCommand({ ping: 1 }).ok ? 0 : 2)'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        MONGODB_URI: mongodb://localhost:27017
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Database Setup

### PostgreSQL Test Database
```bash
# Create test database
sudo -u postgres createdb test_lapis_spider

# Run migrations
DATABASE_URL=postgresql://localhost/test_lapis_spider python -m src.database.setup
```

### MongoDB Test Database
```bash
# Tests will automatically use test_lapis_spider database
# No special setup needed
```

### Redis Test Database
```bash
# Tests use database 1 (production uses 0)
# No special setup needed
```

## Common Test Issues

### Issue: Import Errors
```bash
# Solution: Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Database Connection Failed
```bash
# Check services are running
sudo systemctl status postgresql
sudo systemctl status mongod
sudo systemctl status redis
```

### Issue: Async Test Warnings
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Issue: Slow Tests
```bash
# Run in parallel
pip install pytest-xdist
pytest tests/ -n auto
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Speed**: Mock external services for unit tests
4. **Coverage**: Aim for high coverage but focus on critical paths
5. **Maintenance**: Update tests when code changes

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class LapisSpiderUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "username": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def list_websites(self):
        self.client.get("/websites", headers=self.headers)
    
    @task(3)
    def get_pages(self):
        self.client.get("/content/website-123/pages", headers=self.headers)
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Security Testing

### Run Security Checks
```bash
# Check for security issues
pip install bandit
bandit -r src/

# Check dependencies
pip install safety
safety check
```

## Monitoring Test Health

Track test metrics:
- Test execution time
- Coverage trends
- Flaky test detection
- Performance benchmarks

## Getting Help

If tests fail:
1. Check error messages carefully
2. Verify environment setup
3. Look for recent code changes
4. Check CI/CD logs
5. Ask team for help