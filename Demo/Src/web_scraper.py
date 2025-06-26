import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import requests
from bs4 import BeautifulSoup
import threading
import time
import datetime
import os
import re
import logging
from urllib.parse import urljoin, urlparse
import json
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from results_display_module import ResultsDisplayManager

class WebScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Application")
        
        # Get screen dimensions and set window size
        self.set_window_size()
        
        # Initialize variables
        self.data = []
        self.scraping_active = False
        self.scraping_thread = None
        self.cancel_event = threading.Event()
        
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_gui()
        
        # Headers for web requests - MOVED BEFORE setup_session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Setup requests session with retry strategy
        self.setup_session()
        
        # Alternative search sites (avoiding Google directly)
        self.search_sites = [
            "https://duckduckgo.com/html/?q=",
            "https://www.bing.com/search?q=",
            "https://search.yahoo.com/search?p=",
        ]
        
        # Direct vendor sites for IBM hardware
        self.vendor_sites = [
            "https://www.ibm.com/support/pages/",
            "https://www.ibm.com/docs/",
            "https://www.redbooks.ibm.com/",
        ]
    
    def set_window_size(self):
        """Set window size to fit the current display area"""
        try:
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate window size (using 90% of screen size to leave some margin)
            window_width = int(screen_width * 0.9)
            window_height = int(screen_height * 0.9)
            
            # Ensure minimum dimensions for usability
            min_width = 1200
            min_height = 700
            window_width = max(window_width, min_width)
            window_height = max(window_height, min_height)
            
            # Calculate position to center the window
            pos_x = (screen_width - window_width) // 2
            pos_y = (screen_height - window_height) // 2
            
            # Set geometry (width x height + x_offset + y_offset)
            self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
            
            # Make window resizable
            self.root.resizable(True, True)
            
            # Set minimum window size
            self.root.minsize(min_width, min_height)
            
            # Optional: Start maximized on smaller screens
            if screen_width <= 1366 or screen_height <= 768:
                self.root.state('zoomed')  # Windows
                # For other OS, you might need: self.root.attributes('-zoomed', True)
            
            self.logger.info(f"Window sized to {window_width}x{window_height} for screen {screen_width}x{screen_height}")
            
        except Exception as e:
            # Fallback to default size if there's an error
            self.root.geometry("1400x800")
            print(f"Error setting window size: {e}")
    
    def setup_session(self):
        """Setup requests session with proper configuration"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update(self.headers)
        
        # Disable SSL verification (for testing - not recommended for production)
        self.session.verify = False
    
    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"scraper_log_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Web Scraper Application Started")
    
    def create_gui(self):
        """Create the main GUI with results display on the right"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)  # Left side (input/controls)
        main_frame.columnconfigure(3, weight=1)  # Right side (results)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # File upload section
        ttk.Label(main_frame, text="Upload Input File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path_var, state='readonly', width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Data display section
        ttk.Label(main_frame, text="Input Data:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Treeview for data display
        self.tree_frame = ttk.Frame(main_frame)
        self.tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=('Model',), show='headings', height=8)
        self.tree.heading('Model', text='Hardware Model')
        self.tree.column('Model', width=300)
        
        # Scrollbars for treeview
        tree_scrollbar_v = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel Scraping", command=self.cancel_scraping, state='disabled')
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Progress section
        ttk.Label(main_frame, text="Scraping Progress:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # Progress text area
        self.progress_text = scrolledtext.ScrolledText(main_frame, height=12, width=60)
        self.progress_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(5, weight=1)
        
        # Initialize Results Display Manager on the right side
        self.results_display = ResultsDisplayManager(main_frame, self.logger)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
    
    def browse_file(self):
        """Browse and select input file"""
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.load_data_from_file(file_path)
    
    def load_data_from_file(self, file_path):
        """Load data from the selected file"""
        try:
            self.data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.data.append(line)
            
            # Update treeview
            self.tree.delete(*self.tree.get_children())
            for item in self.data:
                self.tree.insert('', tk.END, values=(item,))
            
            self.status_var.set(f"Loaded {len(self.data)} items")
            self.logger.info(f"Loaded {len(self.data)} items from {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            self.logger.error(f"Failed to load file: {str(e)}")
    
    def start_scraping(self):
        """Start the scraping process"""
        if not self.data:
            messagebox.showwarning("Warning", "Please load input data first!")
            return
        
        # Show confirmation dialog
        if messagebox.askyesno("Confirm", "Starting the scraping for input data. Continue?"):
            self.scraping_active = True
            self.cancel_event.clear()
            self.start_button.config(state='disabled')
            self.cancel_button.config(state='normal')
            self.progress_text.delete(1.0, tk.END)
            
            # Start scraping in a separate thread
            self.scraping_thread = threading.Thread(target=self.scrape_data, daemon=True)
            self.scraping_thread.start()
    
    def cancel_scraping(self):
        """Cancel the scraping process"""
        if self.scraping_active:
            self.cancel_event.set()
            self.update_progress("The Scraping will be Stopped")
            self.logger.info("Scraping cancellation requested")
    
    def update_progress(self, message):
        """Update progress text in thread-safe manner"""
        def update():
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.progress_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.progress_text.see(tk.END)
            self.root.update_idletasks()
        
        self.root.after(0, update)
    
    def clean_text(self, text):
        """Remove HTML tags and clean text"""
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Remove extra whitespace and special characters
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-\./:]', ' ', text)
        
        return text.strip()
    
    def extract_relevant_info(self, text, model):
        """Extract relevant information from scraped text"""
        text_lower = text.lower()
        model_lower = model.lower()
        
        info = {
            'vendor_name': 'Unknown',
            'end_of_sales': 'Not Found',
            'end_of_life': 'Not Found',
            'end_of_service': 'Not Found'
        }
        
        # Extract vendor name
        if 'ibm' in model_lower:
            info['vendor_name'] = 'IBM'
        elif 'dell' in text_lower:
            info['vendor_name'] = 'Dell'
        elif 'hp' in text_lower or 'hewlett' in text_lower:
            info['vendor_name'] = 'HP/HPE'
        
        # Look for date patterns
        date_patterns = [
            r'end.{0,10}of.{0,10}sales?.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'end.{0,10}of.{0,10}life.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'end.{0,10}of.{0,10}service.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'sales?.{0,10}end.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'life.{0,10}end.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'service.{0,10}end.{0,20}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                date_str = match.group(1)
                if 'sales' in match.group(0):
                    info['end_of_sales'] = date_str
                elif 'life' in match.group(0):
                    info['end_of_life'] = date_str
                elif 'service' in match.group(0):
                    info['end_of_service'] = date_str
        
        return info
    
    def scrape_website(self, url, model):
        """Scrape a single website"""
        try:
            self.update_progress(f"Connecting to {urlparse(url).netloc}...")
            
            # Make request with session
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse the content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            cleaned_text = self.clean_text(text_content)
            
            # Check if the content is relevant (contains model number)
            model_clean = re.sub(r'[^\w]', '', model.lower())
            content_clean = re.sub(r'[^\w]', '', cleaned_text.lower())
            
            if model_clean not in content_clean:
                self.logger.info(f"Model {model} not found in content from {url}")
                return None, None
            
            # Extract relevant information
            info = self.extract_relevant_info(cleaned_text, model)
            
            # Create output file
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds
            domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
            filename = f"Scrap_{domain}_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Model: {model}\n")
                f.write(f"Scraped at: {datetime.datetime.utcnow().isoformat()}\n")
                f.write("="*50 + "\n")
                f.write(cleaned_text[:5000])  # Limit content size
            
            self.update_progress(f"Successfully scraped {domain} - saved to {filename}")
            return info, filename
            
        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL Error scraping {url}: {str(e)}")
            self.update_progress(f"SSL Error with {urlparse(url).netloc} - skipping")
            return None, None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request Error scraping {url}: {str(e)}")
            self.update_progress(f"Connection error with {urlparse(url).netloc} - skipping")
            return None, None
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            self.update_progress(f"Error with {urlparse(url).netloc}: {str(e)[:50]}")
            return None, None
    
    def search_model_info(self, model):
        """Search for model information across multiple sites"""
        results = []
        
        # First try direct IBM support search
        self.try_ibm_direct_search(model, results)
        
        if self.cancel_event.is_set():
            return results
        
        # Then try alternative search engines
        for base_url in self.search_sites:
            if self.cancel_event.is_set():
                break
                
            try:
                search_query = f"{model} end of life support date"
                search_url = base_url + search_query.replace(' ', '+')
                
                website_name = urlparse(base_url).netloc or "search_engine"
                self.update_progress(f"Searching {website_name} for {model}")
                
                info, filename = self.scrape_website(search_url, model)
                
                if info and filename:
                    info['url'] = search_url
                    info['filename'] = filename
                    results.append(info)
                    
                # Add delay between requests
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Error searching for {model} on {base_url}: {str(e)}")
                continue
        
        return results
    
    def try_ibm_direct_search(self, model, results):
        """Try to search IBM support directly"""
        try:
            # Create a simple IBM support URL
            ibm_urls = [
                f"https://www.ibm.com/support/pages/search?q={model}",
                f"https://www.ibm.com/docs/search?q={model}",
            ]
            
            for url in ibm_urls:
                if self.cancel_event.is_set():
                    break
                    
                self.update_progress(f"Checking IBM support for {model}")
                info, filename = self.scrape_website(url, model)
                
                if info and filename:
                    info['url'] = url
                    info['filename'] = filename
                    results.append(info)
                
                time.sleep(2)
                
        except Exception as e:
            self.logger.error(f"Error in IBM direct search for {model}: {str(e)}")
    
    def create_mock_data_for_testing(self, model):
        """Create mock data when scraping fails (for testing purposes)"""
        return {
            'vendor_name': 'IBM' if 'IBM' in model else 'Unknown',
            'end_of_sales': 'Check vendor site',
            'end_of_life': 'Check vendor site', 
            'end_of_service': 'Check vendor site',
            'url': 'Manual verification required',
            'filename': f'mock_data_{model.replace(" ", "_")}.txt'
        }
    
    def scrape_data(self):
        """Main scraping function"""
        try:
            self.update_progress("Starting scraping process...")
            self.status_var.set("Scraping in progress...")
            
            all_results = []
            
            for i, model in enumerate(self.data):
                if self.cancel_event.is_set():
                    self.update_progress("Scraping cancelled by user")
                    break
                
                self.update_progress(f"Processing {model} ({i+1}/{len(self.data)})")
                self.logger.info(f"Processing model: {model}")
                
                # Search for model information
                model_results = self.search_model_info(model)
                
                # If no results found, create a placeholder entry
                if not model_results:
                    self.update_progress(f"No data found for {model} - creating placeholder entry")
                    mock_result = self.create_mock_data_for_testing(model)
                    mock_result['model'] = model
                    all_results.append(mock_result)
                else:
                    for result in model_results:
                        result['model'] = model
                        all_results.append(result)
                
                # Update progress
                progress_percent = ((i + 1) / len(self.data)) * 100
                self.status_var.set(f"Progress: {progress_percent:.1f}% - Processing {model}")
            
            # Save summary results
            if all_results:
                self.save_summary_results(all_results)
            
            if not self.cancel_event.is_set():
                self.update_progress("Scraping completed successfully!")
                self.status_var.set("Scraping completed")
                self.logger.info("Scraping completed successfully")
            else:
                self.status_var.set("Scraping cancelled")
                self.logger.info("Scraping was cancelled")
                
        except Exception as e:
            self.update_progress(f"Error during scraping: {str(e)}")
            self.logger.error(f"Error during scraping: {str(e)}")
            self.status_var.set("Scraping failed")
        
        finally:
            self.scraping_active = False
            self.start_button.config(state='normal')
            self.cancel_button.config(state='disabled')
            
            # Load and display results after scraping completes or is cancelled
            self.root.after(1000, self.results_display.on_scraping_complete)
    
    def save_summary_results(self, results):
        """Save summary of all results"""
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"Scraping_Summary_{timestamp}.json"
        
        try:
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.update_progress(f"Summary saved to {summary_filename}")
            self.logger.info(f"Summary saved to {summary_filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving summary: {str(e)}")

def main():
    root = tk.Tk()
    app = WebScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()