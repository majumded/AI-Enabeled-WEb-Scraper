# Web Scraper Application

A Python-based GUI application for scraping hardware lifecycle information from various vendor websites. This tool is specifically designed to gather End-of-Life (EOL), End-of-Sales (EOS), and End-of-Service dates for IBM hardware models and other vendor equipment.

## Features

- **User-friendly GUI**: Built with Tkinter for easy interaction
- **Bulk Processing**: Load hardware models from text files for batch processing
- **Multi-source Scraping**: Searches across multiple platforms including:
  - IBM Support pages
  - IBM Documentation
  - DuckDuckGo
  - Bing
  - Yahoo Search
- **Intelligent Data Extraction**: Automatically identifies vendor names and lifecycle dates
- **Progress Monitoring**: Real-time progress updates and logging
- **Results Management**: Integrated results display and export functionality
- **Robust Error Handling**: Handles SSL errors, connection timeouts, and other network issues
- **Configurable Window Sizing**: Adapts to different screen resolutions

## Prerequisites

### Python Requirements
- Python 3.7 or higher

### Required Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
tkinter
pandas
requests
beautifulsoup4
urllib3
lxml
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/web-scraper-app.git
   cd web-scraper-app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure you have the results display module:**
   - Make sure `results_display_module.py` is in the same directory
   - This module handles the results visualization component

## Usage

### Starting the Application
```bash
python web_scraper.py
```

### Basic Workflow

1. **Load Input Data:**
   - Click "Browse" to select a text file containing hardware models
   - Each line in the file should contain one hardware model name
   - Example input file format:
     ```
     IBM System x3650 M5
     IBM Power Systems S924
     IBM FlashSystem 9100
     ```

2. **Review Loaded Data:**
   - Verify the loaded models in the data display table
   - The application will show how many items were loaded

3. **Start Scraping:**
   - Click "Start Scraping" to begin the process
   - Monitor progress in the progress text area
   - Use "Cancel Scraping" to stop the process if needed

4. **View Results:**
   - Results are displayed in the integrated results panel
   - Individual scraping files are saved with timestamps
   - Summary JSON file is created with all collected data

### Input File Format

Create a text file with hardware models, one per line:
```
IBM System x3650 M5
Dell PowerEdge R740
HP ProLiant DL380 Gen10
IBM Power Systems S924
```

## Output Files

The application generates several types of output files:

### Individual Scraping Files
- **Format**: `Scrap_{domain}_{timestamp}.txt`
- **Content**: Raw scraped data from each website
- **Location**: Same directory as the application

### Summary File
- **Format**: `Scraping_Summary_{timestamp}.json`
- **Content**: Consolidated results from all scrapes
- **Structure**:
  ```json
  [
    {
      "model": "IBM System x3650 M5",
      "vendor_name": "IBM",
      "end_of_sales": "12/31/2020",
      "end_of_life": "12/31/2025",
      "end_of_service": "12/31/2030",
      "url": "https://example.com/source",
      "filename": "Scrap_example_20240101_123456.txt"
    }
  ]
  ```

### Log Files
- **Format**: `scraper_log_{timestamp}.log`
- **Content**: Detailed application logs and error messages

## Configuration

### Headers and User Agent
The application uses realistic browser headers to avoid blocking:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    # ... additional headers
}
```

### Search Sources
Configurable search engines and vendor sites:
- DuckDuckGo HTML search
- Bing search
- Yahoo search
- Direct IBM support pages

### Retry Strategy
Built-in retry mechanism for handling temporary failures:
- 3 total retries
- Exponential backoff
- Handles 429, 500, 502, 503, 504 status codes

## Architecture

### Main Components

1. **WebScraperApp**: Main application class
2. **ResultsDisplayManager**: Handles results visualization (from external module)
3. **Session Management**: Configured requests session with retry logic
4. **Threading**: Non-blocking UI with background scraping operations

### Key Methods

- `scrape_data()`: Main scraping orchestration
- `search_model_info()`: Searches across multiple sources for each model
- `extract_relevant_info()`: Parses scraped content for lifecycle information
- `save_summary_results()`: Consolidates and saves all results

## Error Handling

The application includes comprehensive error handling for:
- SSL certificate issues
- Connection timeouts
- HTTP errors (4xx, 5xx)
- File I/O operations
- Malformed HTML content
- Network connectivity issues

## Limitations

- **Rate Limiting**: Includes delays between requests to avoid overwhelming servers
- **SSL Verification**: Disabled for testing (not recommended for production)
- **Content Parsing**: May not capture all date formats or vendor-specific layouts
- **Search Engine Dependencies**: Relies on external search engines which may change

## Troubleshooting

### Common Issues

1. **"No data found" messages:**
   - Check internet connection
   - Verify input file format
   - Some models may not have publicly available lifecycle information

2. **SSL/Connection errors:**
   - These are logged but don't stop the overall process
   - Application will skip problematic sites and continue

3. **Window sizing issues:**
   - Application auto-detects screen size
   - Minimum window size enforced for usability

### Debug Mode
Check the generated log files for detailed error information and scraping progress.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## Legal and Ethical Considerations

- **Terms of Service**: Ensure compliance with target websites' ToS
- **Rate Limiting**: Built-in delays respect server resources
- **Data Usage**: Only collect publicly available information
- **Attribution**: Properly cite data sources in your usage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the log files for detailed error information
- Ensure all dependencies are properly installed

## Version History

- **v1.0.0**: Initial release with basic scraping functionality
- **v1.1.0**: Added results display integration
- **v1.2.0**: Enhanced error handling and retry logic

---

**Note**: This tool is designed for legitimate research and inventory management purposes. Always respect website terms of service and implement appropriate delays between requests.
