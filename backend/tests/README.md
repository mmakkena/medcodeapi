# Backend Tests

This directory contains the test suite for the Nuvii API backend.

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-asyncio pytest-mock httpx
```

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_billing.py
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_billing.py` - Tests for billing endpoints and Stripe integration
- `test_usage_service.py` - Tests for usage tracking and statistics

## Test Coverage

### Billing Tests (`test_billing.py`)
- ✅ GET /api/v1/billing/subscription - Active subscription
- ✅ GET /api/v1/billing/subscription - No subscription (Free plan)
- ✅ GET /api/v1/billing/subscription - Canceled subscription
- ✅ POST /api/v1/billing/checkout - Successful checkout creation
- ✅ POST /api/v1/billing/checkout - Plan not found
- ✅ POST /api/v1/billing/checkout - Plan without Stripe price
- ✅ GET /api/v1/billing/portal - Successful portal access
- ✅ GET /api/v1/billing/portal - No subscription error
- ✅ POST /api/v1/billing/webhook - Checkout completed event
- ✅ POST /api/v1/billing/webhook - Invalid signature

### Usage Service Tests (`test_usage_service.py`)
- ✅ Usage stats for free tier users
- ✅ Usage stats for users with active subscriptions
- ✅ Correct handling of monthly vs all-time usage
- ✅ Most used endpoint calculation
- ✅ Multiple endpoints tracking
- ✅ Empty stats for new users

## Writing New Tests

When writing new tests, follow these patterns:

1. **Use fixtures** from `conftest.py` for database sessions and auth
2. **Mock external services** (Stripe API calls, etc.)
3. **Test edge cases** (null values, empty data, invalid inputs)
4. **Use descriptive test names** that explain what is being tested
5. **Follow AAA pattern**: Arrange, Act, Assert

### Example Test

```python
@pytest.mark.asyncio
async def test_feature_name(db_session):
    # Arrange
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()

    # Act
    result = await some_function(db_session, user.id)

    # Assert
    assert result["status"] == "success"
```

## Mocking Stripe API

Tests mock Stripe API calls to avoid hitting the actual Stripe API:

```python
@patch('app.api.v1.billing.create_checkout_session')
def test_checkout(mock_create_checkout, client):
    mock_session = Mock()
    mock_session.url = "https://checkout.stripe.com/test"
    mock_create_checkout.return_value = mock_session

    response = client.post("/api/v1/billing/checkout?plan_name=Developer")
    assert response.status_code == 200
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```
