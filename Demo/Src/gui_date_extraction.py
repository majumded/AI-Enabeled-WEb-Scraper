#!/usr/bin/env python3
"""
GUI Interface for Date Extraction Module
Multiple approaches: Tkinter, Web Interface, and API endpoints
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import json
import webbrowser
import os
from datetime import datetime
import sys

# Import the date extraction module
try:
    from date_extraction_module import (
        run_simple_extraction,
        run_advanced_pipeline,
        SimpleDateExtractor,
        DateExtractionPipeline
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False
    print("⚠️  date_extraction_module not found. Please ensure it's in the same directory.")

# =============================================================================
# APPROACH 1: TKINTER GUI (Desktop Application)
# =============================================================================

class DateExtractionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Date Extraction Tool")
        self.root.geometry("800x600")
        
        # Variables
        self.selected_directory = tk.StringVar(value=str(Path.cwd()))
        self.extraction_mode = tk.StringVar(value="advanced")
        self.max_tokens = tk.IntVar(value=3500)
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Date Extraction Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Directory selection
        ttk.Label(main_frame, text="Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.selected_directory)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(dir_frame, text="Browse", 
                  command=self.browse_directory).grid(row=0, column=1)
        
        # Extraction mode
        ttk.Label(main_frame, text="Mode:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Simple (Fast)", 
                       variable=self.extraction_mode, value="simple").grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Advanced (Comprehensive)", 
                       variable=self.extraction_mode, value="advanced").grid(row=0, column=1)
        
        # Max tokens
        ttk.Label(main_frame, text="Max Tokens:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        tokens_frame = ttk.Frame(main_frame)
        tokens_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Spinbox(tokens_frame, from_=1000, to=8000, width=10,
                   textvariable=self.max_tokens).grid(row=0, column=0)
        ttk.Label(tokens_frame, text="(1000-8000)").grid(row=0, column=1, padx=(10, 0))
        
        # Output area
        ttk.Label(main_frame, text="Output:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=70)
        self.output_text.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        # Main extraction button
        self.extract_button = ttk.Button(button_frame, text="🚀 Start Date Extraction", 
                                       command=self.start_extraction, style='Accent.TButton')
        self.extract_button.grid(row=0, column=0, padx=10)
        
        # Additional buttons
        ttk.Button(button_frame, text="📁 Open Output Folder", 
                  command=self.open_output_folder).grid(row=0, column=1, padx=10)
        
        ttk.Button(button_frame, text="📋 View Summary", 
                  command=self.view_summary).grid(row=0, column=2, padx=10)
        
        ttk.Button(button_frame, text="🔄 Clear Output", 
                  command=self.clear_output).grid(row=0, column=3, padx=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Store last result for other operations
        self.last_result = None
        
    def browse_directory(self):
        """Browse for directory containing scrap files"""
        directory = filedialog.askdirectory(initialdir=self.selected_directory.get())
        if directory:
            self.selected_directory.set(directory)
            self.log_output(f"📁 Selected directory: {directory}")
    
    def log_output(self, message):
        """Add message to output area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_output(self):
        """Clear the output area"""
        self.output_text.delete(1.0, tk.END)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def start_extraction(self):
        """Start the extraction process in a separate thread"""
        if not MODULE_AVAILABLE:
            messagebox.showerror("Error", "Date extraction module not available!")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Extraction is already running!")
            return
        
        # Validate directory
        directory = Path(self.selected_directory.get())
        if not directory.exists():
            messagebox.showerror("Error", f"Directory does not exist: {directory}")
            return
        
        # Check for scrap files
        scrap_files = list(directory.glob("Scrap_*.txt"))
        if not scrap_files:
            messagebox.showwarning("Warning", f"No Scrap_*.txt files found in {directory}")
            return
        
        # Start extraction in separate thread
        self.is_running = True
        self.extract_button.config(state='disabled', text="⏳ Processing...")
        self.progress.start()
        
        thread = threading.Thread(target=self.run_extraction, daemon=True)
        thread.start()
    
    def run_extraction(self):
        """Run the actual extraction process"""
        try:
            directory = Path(self.selected_directory.get())
            mode = self.extraction_mode.get()
            max_tokens = self.max_tokens.get()
            
            self.update_status("Starting extraction...")
            self.log_output(f"🔍 Starting {mode} extraction in {directory}")
            self.log_output(f"📊 Max tokens per batch: {max_tokens}")
            
            # Run extraction based on mode
            if mode == "simple":
                extractor = SimpleDateExtractor(max_tokens=max_tokens)
                result = extractor.run(directory=directory, verbose=False)
            else:
                pipeline = DateExtractionPipeline(max_tokens=max_tokens)
                result = pipeline.run_pipeline(directory=directory, verbose=False)
            
            # Update UI in main thread
            self.root.after(0, self.extraction_completed, result)
            
        except Exception as e:
            error_msg = f"Error during extraction: {str(e)}"
            self.root.after(0, self.extraction_error, error_msg)
    
    def extraction_completed(self, result):
        """Handle successful extraction completion"""
        self.is_running = False
        self.extract_button.config(state='normal', text="🚀 Start Date Extraction")
        self.progress.stop()
        self.last_result = result
        
        if result['success']:
            self.update_status("✅ Extraction completed successfully!")
            self.log_output("✅ EXTRACTION COMPLETED SUCCESSFULLY!")
            self.log_output(f"📁 Output directory: {result['output_directory']}")
            self.log_output(f"📝 Prompt files generated: {len(result['prompt_files'])}")
            self.log_output(f"📊 Total dates found: {result['total_dates']}")
            self.log_output(f"📋 Files processed: {result['files_processed']}")
            
            # Show success message
            messagebox.showinfo("Success", 
                              f"Extraction completed!\n\n"
                              f"Files processed: {result['files_processed']}\n"
                              f"Dates found: {result['total_dates']}\n"
                              f"Prompt files: {len(result['prompt_files'])}\n\n"
                              f"Output saved to:\n{result['output_directory']}")
        else:
            self.update_status("❌ Extraction failed")
            self.log_output(f"❌ EXTRACTION FAILED: {result['message']}")
            messagebox.showerror("Extraction Failed", result['message'])
    
    def extraction_error(self, error_msg):
        """Handle extraction error"""
        self.is_running = False
        self.extract_button.config(state='normal', text="🚀 Start Date Extraction")
        self.progress.stop()
        
        self.update_status("❌ Extraction error")
        self.log_output(f"❌ ERROR: {error_msg}")
        messagebox.showerror("Error", error_msg)
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        if self.last_result and self.last_result.get('success'):
            output_dir = self.last_result['output_directory']
            if os.path.exists(output_dir):
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    os.system(f"open '{output_dir}'")
                else:
                    os.system(f"xdg-open '{output_dir}'")
            else:
                messagebox.showerror("Error", f"Output directory not found: {output_dir}")
        else:
            messagebox.showwarning("Warning", "No successful extraction completed yet!")
    
    def view_summary(self):
        """View the comprehensive summary"""
        if self.last_result and self.last_result.get('success'):
            output_dir = Path(self.last_result['output_directory'])
            summary_files = list(output_dir.glob("comprehensive_summary_*.json"))
            
            if summary_files:
                summary_file = summary_files[0]
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                    
                    # Create summary window
                    self.show_summary_window(summary_data)
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read summary: {e}")
            else:
                messagebox.showwarning("Warning", "Summary file not found!")
        else:
            messagebox.showwarning("Warning", "No successful extraction completed yet!")
    
    def show_summary_window(self, summary_data):
        """Show summary in a new window"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Extraction Summary")
        summary_window.geometry("600x500")
        
        # Summary text
        text_area = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format summary for display
        summary_text = f"""EXTRACTION SUMMARY
{'='*50}

Processing Time: {summary_data.get('processing_timestamp_utc', 'N/A')}
Session ID: {summary_data.get('extraction_session_id', 'N/A')}

FILES SUMMARY:
• Total files processed: {summary_data.get('total_files_processed', 0)}
• Files with dates: {summary_data.get('files_with_dates', 0)}
• Files without dates: {summary_data.get('files_without_dates', 0)}
• Total dates found: {summary_data.get('total_dates_found', 0)}

OUTPUT:
• Output directory: {summary_data.get('output_directory', 'N/A')}
• Prompt batches: {summary_data.get('prompt_batches_created', 0)}

FILE DETAILS:
"""
        
        for i, file_detail in enumerate(summary_data.get('file_details', []), 1):
            summary_text += f"\n{i}. {file_detail.get('scrap_file_name', 'Unknown')}\n"
            summary_text += f"   URL: {file_detail.get('source_url', 'N/A')}\n"
            summary_text += f"   Dates found: {file_detail.get('dates_found_count', 0)}\n"
            summary_text += f"   Has dates: {'Yes' if file_detail.get('has_business_dates', False) else 'No'}\n"
        
        text_area.insert(tk.END, summary_text)
        text_area.config(state=tk.DISABLED)

# =============================================================================
# APPROACH 2: SIMPLE BUTTON INTEGRATION
# =============================================================================

class SimpleButtonIntegration:
    """Simple class that can be integrated into existing applications"""
    
    def __init__(self, parent_widget=None):
        self.parent = parent_widget
        self.last_result = None
    
    def create_extraction_button(self, parent_frame):
        """Create a button that can be added to any tkinter frame"""
        button = ttk.Button(parent_frame, 
                          text="📅 Extract Dates from Scrap Files",
                          command=self.quick_extraction)
        return button
    
    def quick_extraction(self):
        """Quick extraction with minimal UI"""
        try:
            # Ask for directory
            directory = filedialog.askdirectory(title="Select directory with Scrap_*.txt files")
            if not directory:
                return
            
            # Show progress dialog
            progress_window = self.show_progress_dialog()
            
            # Run extraction
            result = run_advanced_pipeline(directory=Path(directory), verbose=False)
            
            # Close progress dialog
            progress_window.destroy()
            
            # Show results
            if result['success']:
                messagebox.showinfo("Success", 
                                  f"✅ Date extraction completed!\n\n"
                                  f"📊 Files processed: {result['files_processed']}\n"
                                  f"📅 Dates found: {result['total_dates']}\n"
                                  f"📝 Prompt files: {len(result['prompt_files'])}\n\n"
                                  f"📁 Output: {result['output_directory']}")
                
                # Ask if user wants to open output folder
                if messagebox.askyesno("Open Folder", "Would you like to open the output folder?"):
                    self.open_folder(result['output_directory'])
            else:
                messagebox.showerror("Failed", f"❌ Extraction failed:\n{result['message']}")
            
            self.last_result = result
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
    
    def show_progress_dialog(self):
        """Show a simple progress dialog"""
        progress_window = tk.Toplevel()
        progress_window.title("Processing...")
        progress_window.geometry("300x100")
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="🔍 Extracting dates from files...").pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        # Center the window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
        y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        return progress_window
    
    def open_folder(self, folder_path):
        """Open folder in system file manager"""
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                os.system(f"open '{folder_path}'")
            else:
                os.system(f"xdg-open '{folder_path}'")
        except Exception as e:
            print(f"Could not open folder: {e}")

# =============================================================================
# APPROACH 3: CALLBACK-BASED INTEGRATION
# =============================================================================

class CallbackBasedExtraction:
    """Extraction with callbacks for integration into existing applications"""
    
    def __init__(self, 
                 on_start=None, 
                 on_progress=None, 
                 on_success=None, 
                 on_error=None,
                 on_complete=None):
        self.on_start = on_start
        self.on_progress = on_progress
        self.on_success = on_success
        self.on_error = on_error
        self.on_complete = on_complete
    
    def extract_dates(self, directory, mode="advanced", max_tokens=3500):
        """Extract dates with callbacks"""
        try:
            # Notify start
            if self.on_start:
                self.on_start(f"Starting {mode} extraction in {directory}")
            
            # Progress callback
            if self.on_progress:
                self.on_progress("Initializing extraction...")
            
            # Run extraction
            if mode == "simple":
                extractor = SimpleDateExtractor(max_tokens=max_tokens)
                result = extractor.run(directory=Path(directory), verbose=False)
            else:
                pipeline = DateExtractionPipeline(max_tokens=max_tokens)
                result = pipeline.run_pipeline(directory=Path(directory), verbose=False)
            
            # Notify completion
            if result['success']:
                if self.on_success:
                    self.on_success(result)
            else:
                if self.on_error:
                    self.on_error(result['message'])
            
            if self.on_complete:
                self.on_complete(result)
            
            return result
            
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
            if self.on_complete:
                self.on_complete({'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def example_full_gui():
    """Example: Full GUI application"""
    root = tk.Tk()
    app = DateExtractionGUI(root)
    root.mainloop()

def example_simple_integration():
    """Example: Simple button integration"""
    root = tk.Tk()
    root.title("My Application")
    root.geometry("400x200")
    
    # Your existing application widgets
    ttk.Label(root, text="My Application", font=('Arial', 14)).pack(pady=20)
    
    # Add the date extraction button
    integration = SimpleButtonIntegration(root)
    extract_button = integration.create_extraction_button(root)
    extract_button.pack(pady=10)
    
    # Your other widgets
    ttk.Button(root, text="Other Function").pack(pady=5)
    
    root.mainloop()

def example_callback_integration():
    """Example: Callback-based integration"""
    
    def on_extraction_start(message):
        print(f"🚀 Started: {message}")
    
    def on_extraction_progress(message):
        print(f"⏳ Progress: {message}")
    
    def on_extraction_success(result):
        print(f"✅ Success! Found {result['total_dates']} dates")
        print(f"📁 Output: {result['output_directory']}")
    
    def on_extraction_error(error_message):
        print(f"❌ Error: {error_message}")
    
    def on_extraction_complete(result):
        print("🏁 Extraction process completed")
    
    # Create extractor with callbacks
    extractor = CallbackBasedExtraction(
        on_start=on_extraction_start,
        on_progress=on_extraction_progress,
        on_success=on_extraction_success,
        on_error=on_extraction_error,
        on_complete=on_extraction_complete
    )
    
    # Run extraction
    result = extractor.extract_dates("./test_data", mode="advanced")
    return result

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
    else:
        print("Choose example:")
        print("1. Full GUI application")
        print("2. Simple button integration")
        print("3. Callback-based integration")
        example_type = input("Enter choice (1-3, default=1): ").strip() or "1"
    
    if example_type == "1":
        example_full_gui()
    elif example_type == "2":
        example_simple_integration()
    elif example_type == "3":
        example_callback_integration()
    else:
        print("Invalid choice. Running full GUI...")
        example_full_gui()
