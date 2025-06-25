# Web Scraper Application

AI Enabeled WEb Scraper - UI
![AI Enabeled WEb Scraper - UI](https://github.com/majumded/AI-Enabeled-WEb-Scraper/blob/main/Scraper%20Main%20UI.JPG)

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

# GUI Date Extraction Tool (Prompt File Creator)

Prompt File Creator - UI
![Prompt File Creator - UI](https://github.com/majumded/AI-Enabeled-WEb-Scraper/blob/main/Prompt%20Creator%20UI.JPG)

A comprehensive Python GUI application for extracting business-critical dates from scraped web content. This tool processes Scrap_*.txt files and generates structured prompts for AI-based date extraction, specifically designed for hardware lifecycle management and EOL (End-of-Life) date discovery.

## 🌟 Features

### Core Functionality
- **Batch Processing**: Process multiple Scrap_*.txt files simultaneously
- **Dual Extraction Modes**: Simple (fast) and Advanced (comprehensive) processing
- **Intelligent Date Recognition**: Extracts End-of-Life, End-of-Sales, and End-of-Service dates
- **AI-Ready Output**: Generates structured prompts for large language model processing
- **Real-time Progress Monitoring**: Live updates and comprehensive logging

### GUI Options
- **Full Desktop Application**: Complete Tkinter-based interface
- **Simple Integration**: Single-button component for existing applications
- **Callback-based Processing**: Event-driven architecture for custom integrations

### Advanced Features
- **Token Management**: Configurable batch sizes (1000-8000 tokens)
- **Comprehensive Reporting**: Detailed JSON summaries and statistics
- **Cross-platform Compatibility**: Windows, macOS, and Linux support
- **Error Handling**: Robust error recovery and detailed logging

## 📋 Prerequisites

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB recommended for large datasets)

### Required Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
tkinter
pathlib
json
threading
datetime
webbrowser
os
sys
```

### Core Module Dependency
The application requires the `date_extraction_module.py` to be present in the same directory:
```
date_extraction_module.py  # Core extraction logic
gui_date_extraction.py     # GUI interface
```

## 🚀 Installation

### 1. Clone or Download
```bash
git clone https://github.com/yourusername/gui-date-extraction.git
cd gui-date-extraction
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Module Structure
Ensure your directory contains:
```
📁 project-directory/
├── 📄 gui_date_extraction.py
├── 📄 date_extraction_module.py
├── 📄 requirements.txt
├── 📄 README.md
└── 📁 Scrap_files/
    ├── 📄 Scrap_example_20240101_123456.txt
    ├── 📄 Scrap_vendor_20240101_123457.txt
    └── 📄 ...
```

## 💻 Usage

### Method 1: Full GUI Application (Recommended)

#### Start the Application
```bash
python gui_date_extraction.py
```

#### Basic Workflow
1. **Select Directory**: Browse to folder containing Scrap_*.txt files
2. **Choose Mode**: 
   - **Simple**: Fast processing, basic date extraction
   - **Advanced**: Comprehensive analysis with detailed context
3. **Configure Settings**: Set max tokens per batch (1000-8000)
4. **Start Extraction**: Click "🚀 Start Date Extraction"
5. **Monitor Progress**: Watch real-time processing updates
6. **Review Results**: Use built-in summary viewer and file explorer

#### GUI Interface Overview
```
┌─────────────────────────────────────────────────────────┐
│                 Date Extraction Tool                   │
├─────────────────────────────────────────────────────────┤
│ Directory: [/path/to/scrap/files]     [Browse]         │
│ Mode: ○ Simple (Fast) ● Advanced (Comprehensive)       │
│ Max Tokens: [3500] (1000-8000)                        │
├─────────────────────────────────────────────────────────┤
│ Output:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [12:34:56] 📁 Selected directory: /path/to/files   │ │
│ │ [12:34:58] 🔍 Starting advanced extraction...      │ │
│ │ [12:35:02] ✅ Processing complete!                 │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ [🚀 Start] [📁 Open Folder] [📋 Summary] [🔄 Clear]    │
├─────────────────────────────────────────────────────────┤
│ Status: ✅ Extraction completed successfully!           │
│ ████████████████████████████████████████████████████   │
└─────────────────────────────────────────────────────────┘
```

### Method 2: Simple Integration

For integrating into existing applications:

```python
from gui_date_extraction import SimpleButtonIntegration

# In your existing tkinter application
integration = SimpleButtonIntegration(parent_widget)
extract_button = integration.create_extraction_button(your_frame)
extract_button.pack()
```

### Method 3: Callback-based Integration

For custom event handling:

```python
from gui_date_extraction import CallbackBasedExtraction

def on_success(result):
    print(f"Found {result['total_dates']} dates!")

extractor = CallbackBasedExtraction(on_success=on_success)
result = extractor.extract_dates("/path/to/directory")
```

## 📂 Input File Format

### Expected File Structure
The application processes files matching the pattern `Scrap_*.txt`:

```
Scrap_ibm_com_20240101_123456.txt
Scrap_vendor_site_20240101_123457.txt
Scrap_support_page_20240101_123458.txt
```

### File Content Format
Each Scrap file should contain:
```
URL: https://example.com/hardware-model
Model: IBM System x3650 M5
Scraped at: 2024-01-01T12:34:56
==================================================
[Raw scraped content containing dates and lifecycle information]
```

## 📊 Output Files

### Generated Prompt Files
**Format**: `prompt_batch_YYYYMMDD_HHMMSS_X.txt`
```
prompt_batch_20240101_123456_1.txt
prompt_batch_20240101_123456_2.txt
prompt_batch_20240101_123456_3.txt
```

**Content Structure**:
```
BATCH PROCESSING REQUEST - BUSINESS DATE EXTRACTION
==================================================

OBJECTIVE: Extract business-critical dates from hardware vendor documentation

INSTRUCTIONS:
1. Identify End-of-Life (EOL) dates
2. Identify End-of-Sales (EOS) dates  
3. Identify End-of-Service dates
4. Extract in YYYY-MM-DD format
5. Provide confidence levels

FILES TO PROCESS:
==================================================

FILE 1: Scrap_example_20240101_123456.txt
URL: https://example.com/hardware
MODEL: IBM System x3650 M5
CONTENT:
[Extracted and cleaned content...]

[Additional files...]
```

### Summary Reports
**Format**: `comprehensive_summary_YYYYMMDD_HHMMSS.json`

```json
{
  "extraction_session_id": "session_20240101_123456",
  "processing_timestamp_utc": "2024-01-01T12:34:56Z",
  "total_files_processed": 15,
  "files_with_dates": 12,
  "files_without_dates": 3,
  "total_dates_found": 36,
  "prompt_batches_created": 3,
  "output_directory": "/path/to/output",
  "file_details": [
    {
      "scrap_file_name": "Scrap_ibm_com_20240101_123456.txt",
      "source_url": "https://ibm.com/support/...",
      "dates_found_count": 3,
      "has_business_dates": true,
      "extracted_dates": [
        "2025-12-31",
        "2026-06-30",
        "2027-12-31"
      ]
    }
  ]
}
```

## ⚙️ Configuration Options

### Extraction Modes

#### Simple Mode (Fast)
- **Processing Speed**: ~2-3 files per second
- **Token Usage**: Optimized for basic date extraction
- **Use Case**: Quick processing of large datasets
- **Output Quality**: Standard date identification

#### Advanced Mode (Comprehensive)
- **Processing Speed**: ~1 file per second
- **Token Usage**: Detailed context preservation
- **Use Case**: Thorough analysis requiring high accuracy
- **Output Quality**: Enhanced context and confidence scoring

### Token Configuration
- **Range**: 1000-8000 tokens per batch
- **Default**: 3500 tokens
- **Recommendation**: 
  - Small files (< 2KB): 1000-2000 tokens
  - Medium files (2-10KB): 3000-4000 tokens
  - Large files (> 10KB): 5000-8000 tokens

## 🔧 Advanced Integration

### Custom Callback Implementation

```python
class MyDateExtractor:
    def __init__(self):
        self.progress_callback = self.update_progress
        self.success_callback = self.handle_success
        
    def update_progress(self, message):
        # Update your application's progress bar
        self.progress_bar.set_text(message)
        
    def handle_success(self, result):
        # Process the extraction results
        self.display_results(result['total_dates'])
        
    def run_extraction(self):
        extractor = CallbackBasedExtraction(
            on_progress=self.progress_callback,
            on_success=self.success_callback
        )
        return extractor.extract_dates(self.directory_path)
```

### Command Line Usage

```bash
# Full GUI
python gui_date_extraction.py

# Simple integration example
python gui_date_extraction.py 2

# Callback example
python gui_date_extraction.py 3
```

## 📈 Performance Optimization

### Recommended Settings by Dataset Size

| Dataset Size | Mode | Max Tokens | Expected Time |
|--------------|------|------------|---------------|
| < 50 files | Advanced | 3500 | 1-2 minutes |
| 50-200 files | Advanced | 4000 | 3-8 minutes |
| 200-500 files | Simple | 3000 | 5-10 minutes |
| > 500 files | Simple | 2500 | 10+ minutes |

### Memory Usage Guidelines
- **Simple Mode**: ~50MB per 100 files
- **Advanced Mode**: ~150MB per 100 files
- **Batch Processing**: Memory usage scales linearly

## 🛠️ Troubleshooting

### Common Issues

#### "date_extraction_module not found"
**Solution**: Ensure `date_extraction_module.py` is in the same directory
```bash
ls -la | grep date_extraction_module.py
```

#### "No Scrap_*.txt files found"
**Solutions**:
1. Verify file naming convention: `Scrap_*.txt`
2. Check directory permissions
3. Ensure files contain actual content (not empty)

#### "Extraction failed" or Low Success Rate
**Solutions**:
1. Increase max tokens for complex content
2. Switch to Advanced mode for better accuracy
3. Verify input files contain date-related content
4. Check file encoding (should be UTF-8)

#### GUI Performance Issues
**Solutions**:
1. Reduce max tokens per batch
2. Process smaller datasets in chunks
3. Close other resource-intensive applications
4. Use Simple mode for faster processing

### Debug Mode

Enable detailed logging by modifying the script:
```python
# Add at the beginning of gui_date_extraction.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🧪 Testing

### Test Dataset Creation
Create test Scrap files:
```bash
mkdir test_data
echo "URL: https://example.com
Model: Test Model 
End of Life: 2025-12-31
End of Sales: 2024-06-30" > test_data/Scrap_test_20240101_123456.txt
```

### Validation Steps
1. **File Recognition**: Verify files are detected
2. **Content Processing**: Check extraction accuracy
3. **Output Generation**: Validate prompt file format
4. **Summary Creation**: Confirm JSON structure

## 🔒 Security Considerations

### Data Privacy
- **Local Processing**: All data remains on your system
- **No Network Calls**: Application works offline
- **File Permissions**: Standard read/write access required

### Input Validation
- **File Size Limits**: Large files (>50MB) may cause memory issues
- **Content Filtering**: Automatically handles malformed HTML/text
- **Path Validation**: Prevents directory traversal attacks

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Install development dependencies: `pip install -r dev-requirements.txt`
4. Make changes and test thoroughly
5. Submit pull request with detailed description

### Code Style Guidelines
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations where appropriate
- **Documentation**: Include docstrings for all functions
- **Testing**: Add unit tests for new features

### Feature Requests
- **Issue Templates**: Use provided GitHub issue templates
- **Enhancement Proposals**: Include use cases and mockups
- **Performance Improvements**: Provide benchmarks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check this README and inline comments
- **Examples**: Review the usage examples in the code

### Community Resources
- **Wiki**: Additional tutorials and advanced usage
- **Discussions**: Community Q&A and best practices
- **Releases**: Version history and breaking changes

## 📚 Related Projects

- **Web Scraper Application**: Generates the Scrap_*.txt input files
- **Date Extraction Module**: Core processing engine
- **Hardware Lifecycle Database**: Stores extracted date information

## 🔄 Version History

- **v2.0.0**: Full GUI implementation with multiple integration options
- **v1.5.0**: Added callback-based architecture
- **v1.0.0**: Initial simple button integration
- **v0.9.0**: Beta release with basic functionality

---

**Note**: This tool is designed for processing publicly available hardware lifecycle information. Always ensure compliance with website terms of service and data usage policies when using scraped content.
