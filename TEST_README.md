# Name That Yankee - Test Suite

This comprehensive test suite covers all major functionality of the Name That Yankee application.

## Test Categories

### 1. Overall Site Structure Tests (`TestSiteStructure`)
- **Purpose**: Ensures core site components load correctly
- **Tests**: Main page layout, navigation links, gallery cards, responsive design
- **Coverage**: Header, footer, search bar, gallery, navigation elements

### 2. Search Functionality Tests (`TestSearchFunctionality`)
- **Purpose**: Validates search and filtering capabilities
- **Tests**: Date search, year search, team search, unsolved filter, no results handling
- **Coverage**: Search bar, checkbox filter, results display

### 3. Quiz Functionality Tests (`TestQuizFunctionality`)
- **Purpose**: Tests quiz game mechanics and scoring
- **Tests**: Quiz page loading, scoring system, hints, max guesses, input validation
- **Coverage**: Quiz interface, scoring logic, hint system, guess limits

### 4. Security Tests (`TestSecurity`)
- **Purpose**: Identifies potential security vulnerabilities
- **Tests**: XSS prevention, SQL injection prevention, localStorage security, input sanitization
- **Coverage**: Input validation, data sanitization, secure storage

### 5. Analytics Page Tests (`TestAnalyticsPage`)
- **Purpose**: Validates analytics page functionality
- **Tests**: Page loading, chart rendering, data accuracy, navigation
- **Coverage**: Analytics interface, chart display, data consistency

### 6. Utility Tests (`TestUtilities`)
- **Purpose**: Additional edge cases and compatibility
- **Tests**: Browser compatibility, performance, accessibility
- **Coverage**: Cross-browser support, performance metrics, accessibility standards

## Setup Instructions

### Prerequisites
1. **Python 3.8+** installed
2. **Chrome browser** installed (for Selenium tests)
3. **Local web server** running on port 8000

### Installation
```bash
# Install test dependencies
pip install -r test_requirements.txt

# Start your local web server
cd /path/to/your/NameThatYankee/project
python -m http.server 8000
```

### Required Web Server
The test suite requires your local web server to be running:
- **URL**: `http://localhost:8000/`
- **Command**: `python -m http.server 8000`
- **Directory**: Your NameThatYankee project root

This allows Firebase and other external services to work properly during testing.

## Running Tests

### Run All Tests
```bash
pytest test_yankee_site.py -v
```

### Run Specific Test Categories
```bash
# Site structure tests only
pytest test_yankee_site.py::TestSiteStructure -v

# Search functionality tests only
pytest test_yankee_site.py::TestSearchFunctionality -v

# Quiz functionality tests only
pytest test_yankee_site.py::TestQuizFunctionality -v

# Security tests only
pytest test_yankee_site.py::TestSecurity -v

# Analytics tests only
pytest test_yankee_site.py::TestAnalyticsPage -v
```

### Run Individual Tests
```bash
# Specific test
pytest test_yankee_site.py::TestSiteStructure::test_main_page_loads_correctly -v

# Tests matching a pattern
pytest test_yankee_site.py -k "search" -v
```

### Advanced Options
```bash
# Run with detailed output
pytest test_yankee_site.py -v -s

# Run in parallel (requires pytest-xdist)
pytest test_yankee_site.py -n auto

# Generate HTML report
pytest test_yankee_site.py --html=report.html --self-contained-html
```

## Test Configuration

### Browser Options
The test suite uses Chrome with these options:
- `--no-sandbox` - Required for CI environments
- `--disable-dev-shm-usage` - Prevents memory issues
- `--disable-gpu` - Disables GPU acceleration
- `--window-size=1920,1080` - Sets consistent window size

### Wait Strategies
- **Implicit wait**: 5 seconds for element location
- **Explicit wait**: 10 seconds for specific conditions
- **Sleep delays**: Used for dynamic content loading

## Test Data Requirements

### For Quiz Tests
- Quiz pages must have proper URL parameters (`?date=YYYY-MM-DD`)
- Quiz data must be embedded in the page (quiz-data div)
- Correct answers must be available for validation

### For Search Tests
- Gallery containers must have proper `data-search-terms` attributes
- Search functionality must be implemented in JavaScript
- Filter checkboxes must be functional

### For Analytics Tests
- Analytics page must load Firebase and Chart.js
- Chart containers must be present
- Loading states must be properly handled

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   ```bash
   # Update webdriver-manager
   pip install --upgrade webdriver-manager
   ```

2. **Web Server Not Running**
   ```bash
   # Start the web server in your project directory
   cd /path/to/NameThatYankee
   python -m http.server 8000
   
   # In another terminal, run tests
   pytest test_yankee_site.py -v
   ```

3. **Timeout Issues**
   - Increase wait times in test configuration
   - Check for slow loading elements
   - Verify test data files are accessible

4. **Element Not Found**
   - Verify HTML structure matches test expectations
   - Check for dynamic content loading
   - Ensure proper element IDs and classes

### Debug Mode
```bash
# Run with browser visible (not headless)
pytest test_yankee_site.py -v -s --headed

# Pause on failures
pytest test_yankee_site.py -v -s --pdb
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r test_requirements.txt
    - name: Run tests
      run: |
        pytest test_yankee_site.py -v
```

## Contributing

When adding new tests:
1. Follow the existing class structure
2. Add descriptive docstrings
3. Use appropriate wait strategies
4. Include both positive and negative test cases
5. Update this README if adding new test categories

## Test Coverage Goals

- **Site Structure**: 100% of core elements
- **Search Functionality**: All search types and filters
- **Quiz Functionality**: All game mechanics and edge cases
- **Security**: Common vulnerability vectors
- **Analytics**: Chart rendering and data display
- **Utilities**: Performance and accessibility basics
