import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import pandas as pd
import os
import glob
from datetime import datetime

class ResultsDisplayManager:
    """Manages the display and export of scraping results"""
    
    def __init__(self, parent_frame, logger=None):
        self.parent_frame = parent_frame
        self.logger = logger
        self.results_data = []
        self.raw_data = None  # Store the original JSON data
        self.latest_json_file = None
        self.create_results_display()
    
    def create_results_display(self):
        """Create the results display section on the right side of the UI"""
        # Results frame (right side)
        self.results_frame = ttk.LabelFrame(self.parent_frame, text="File Details Results", padding="5")
        self.results_frame.grid(row=0, column=3, rowspan=7, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=5)
        
        # Configure the results frame
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(2, weight=1)  # Changed to row 2 for table
        
        # Results info label
        self.results_info_var = tk.StringVar()
        self.results_info_var.set("No results to display")
        self.results_info_label = ttk.Label(self.results_frame, textvariable=self.results_info_var)
        self.results_info_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Buttons frame (moved up)
        self.buttons_frame = ttk.Frame(self.results_frame)
        self.buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.buttons_frame.columnconfigure(0, weight=1)
        
        # Download button
        self.download_button = ttk.Button(
            self.buttons_frame, 
            text="Download as CSV", 
            command=self.download_csv,
            state='disabled'
        )
        self.download_button.grid(row=0, column=0, sticky=tk.W)
        
        # Refresh button
        self.refresh_button = ttk.Button(
            self.buttons_frame, 
            text="Refresh Results", 
            command=self.load_latest_results
        )
        self.refresh_button.grid(row=0, column=1, sticky=tk.E)
        
        # Create treeview for results display
        self.create_results_table()
    
    def create_results_table(self):
        """Create the results table (treeview)"""
        # Frame for the treeview and scrollbars
        self.table_frame = ttk.Frame(self.results_frame)
        self.table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)
        
        # Define columns for file details
        columns = ('Scrap File Name', 'Scrap File Location', 'Source URL', 'Prompt File Name', 'Prompt File Path', 'Batch Number')
        
        # Create treeview with horizontal and vertical scrolling
        self.results_tree = ttk.Treeview(
            self.table_frame, 
            columns=columns, 
            show='headings', 
            height=12  # Reduced height to accommodate buttons
        )
        
        # Configure column headings and widths
        column_widths = {
            'Scrap File Name': 200,
            'Scrap File Location': 250,
            'Source URL': 300,
            'Prompt File Name': 200,
            'Prompt File Path': 250,
            'Batch Number': 80
        }
        
        # Configure column-specific minimum widths
        column_minwidths = {
            'Scrap File Name': 150,
            'Scrap File Location': 180,
            'Source URL': 200,
            'Prompt File Name': 150,
            'Prompt File Path': 180,
            'Batch Number': 60
        }
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            minwidth = column_minwidths.get(col, 70)
            self.results_tree.column(col, width=column_widths.get(col, 100), minwidth=minwidth, stretch=True)
        
        # Bind double-click event
        self.results_tree.bind('<Double-1>', self.on_row_double_click)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        
        # Configure scrollbars
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for table and scrollbars
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def on_row_double_click(self, event):
        """Handle double-click on a table row"""
        # Get selected item
        selection = self.results_tree.selection()
        if not selection:
            return
        
        # Get the index of the selected item
        item_id = selection[0]
        item_index = self.results_tree.index(item_id)
        
        # Get the corresponding data from results_data
        if 0 <= item_index < len(self.results_data):
            record_data = self.results_data[item_index]
            self.show_record_popup(record_data)
    
    def open_file_in_notepad(self, file_path):
        """Open a file in a notepad-like window"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File not found:\n{file_path}")
                return
            
            # Create notepad window
            notepad_window = tk.Toplevel(self.parent_frame)
            notepad_window.title(f"File Viewer - {os.path.basename(file_path)}")
            notepad_window.geometry("800x600")
            notepad_window.resizable(True, True)
            
            # Make notepad window modal
            notepad_window.transient(self.parent_frame.winfo_toplevel())
            notepad_window.grab_set()
            
            # Center the notepad window
            notepad_window.update_idletasks()
            x = (notepad_window.winfo_screenwidth() // 2) - (notepad_window.winfo_width() // 2)
            y = (notepad_window.winfo_screenheight() // 2) - (notepad_window.winfo_height() // 2)
            notepad_window.geometry(f"+{x}+{y}")
            
            # Main frame
            main_frame = ttk.Frame(notepad_window, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configure grid weights
            notepad_window.columnconfigure(0, weight=1)
            notepad_window.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=1)
            
            # Path label only
            path_label = ttk.Label(main_frame, text=f"Path: {file_path}", font=('TkDefaultFont', 9))
            path_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
            
            # Create frame for the text widget and scrollbars
            text_frame = ttk.Frame(main_frame)
            text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
            text_frame.columnconfigure(0, weight=1)
            text_frame.rowconfigure(0, weight=1)
            
            # Create text widget with scrollbars
            text_widget = tk.Text(
                text_frame, 
                wrap=tk.WORD, 
                font=('Consolas', 10),
                background='white',
                foreground='black',
                selectbackground='lightblue'
            )
            
            v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
            
            text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Grid layout for text widget and scrollbars
            text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
            
            # Read and display file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                text_widget.insert(tk.END, content)
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                    text_widget.insert(tk.END, content)
                except Exception as e:
                    text_widget.insert(tk.END, f"Error reading file: {str(e)}")
            except Exception as e:
                text_widget.insert(tk.END, f"Error reading file: {str(e)}")
            
            # Make text widget read-only by default, but allow selection
            text_widget.config(state=tk.DISABLED)
            
            # Buttons frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
            
            # Maximize button
            def toggle_maximize():
                if notepad_window.state() == 'zoomed':
                    notepad_window.state('normal')
                    maximize_button.config(text="Maximize")
                else:
                    notepad_window.state('zoomed')
                    maximize_button.config(text="Restore")
            
            maximize_button = ttk.Button(button_frame, text="Maximize", command=toggle_maximize)
            maximize_button.grid(row=0, column=0, padx=(0, 5))
            
            # Select all button
            def select_all():
                text_widget.config(state=tk.NORMAL)
                text_widget.tag_add(tk.SEL, "1.0", tk.END)
                text_widget.mark_set(tk.INSERT, "1.0")
                text_widget.see(tk.INSERT)
                text_widget.config(state=tk.DISABLED)
                text_widget.focus_set()
            
            select_all_button = ttk.Button(button_frame, text="Select All", command=select_all)
            select_all_button.grid(row=0, column=1, padx=5)
            
            # Copy selected button
            def copy_selected():
                try:
                    selected_text = text_widget.selection_get()
                    notepad_window.clipboard_clear()
                    notepad_window.clipboard_append(selected_text)
                    messagebox.showinfo("Copied", "Selected text copied to clipboard")
                except tk.TclError:
                    messagebox.showwarning("Warning", "No text selected")
            
            copy_selected_button = ttk.Button(button_frame, text="Copy Selected", command=copy_selected)
            copy_selected_button.grid(row=0, column=2, padx=5)
            
            # Copy all button
            def copy_all():
                all_text = text_widget.get("1.0", tk.END)
                notepad_window.clipboard_clear()
                notepad_window.clipboard_append(all_text)
                messagebox.showinfo("Copied", "All text copied to clipboard")
            
            copy_all_button = ttk.Button(button_frame, text="Copy All", command=copy_all)
            copy_all_button.grid(row=0, column=3, padx=5)
            
            # Close button
            close_button = ttk.Button(button_frame, text="Close", command=notepad_window.destroy)
            close_button.grid(row=0, column=4, padx=(5, 0))
            
            # Bind Ctrl+A to select all
            def ctrl_a(event):
                select_all()
                return "break"
            
            notepad_window.bind('<Control-a>', ctrl_a)
            
            # Bind Ctrl+C to copy selected
            def ctrl_c(event):
                copy_selected()
                return "break"
            
            notepad_window.bind('<Control-c>', ctrl_c)
            
            # Bind Escape key to close
            notepad_window.bind('<Escape>', lambda e: notepad_window.destroy())
            
            # Focus on the text widget
            text_widget.focus_set()
            
            if self.logger:
                self.logger.info(f"Opened file in notepad viewer: {file_path}")
                
        except Exception as e:
            error_msg = f"Error opening file: {str(e)}"
            messagebox.showerror("Error", error_msg)
            if self.logger:
                self.logger.error(f"Error opening file {file_path}: {str(e)}")
    
    def show_record_popup(self, record_data):
        """Show a popup window with detailed record information"""
        # Create popup window
        popup = tk.Toplevel(self.parent_frame)
        popup.title("File Details")
        popup.geometry("700x500")
        popup.resizable(True, True)
        
        # Make popup modal
        popup.transient(self.parent_frame.winfo_toplevel())
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="File Details", font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # Create frame for the listbox and scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create listbox with scrollbar
        listbox = tk.Listbox(list_frame, font=('Consolas', 10), selectmode=tk.SINGLE)
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=listbox.xview)
        
        listbox.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Grid layout for listbox and scrollbars
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Populate listbox with record data
        field_order = ['scrap_file_name', 'scrap_file_location', 'source_url', 'prompt_file_name', 'prompt_file_path', 'batch_number']
        
        for field in field_order:
            if field in record_data:
                value = record_data[field]
                display_text = f"{field.replace('_', ' ').title()}: {value}"
                listbox.insert(tk.END, display_text)
        
        # Add any additional fields not in the standard order
        for key, value in record_data.items():
            if key not in field_order:
                display_text = f"{key.replace('_', ' ').title()}: {value}"
                listbox.insert(tk.END, display_text)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Copy selected line button
        def copy_selected_line():
            selection = listbox.curselection()
            if selection:
                selected_text = listbox.get(selection[0])
                popup.clipboard_clear()
                popup.clipboard_append(selected_text)
                messagebox.showinfo("Copied", f"Copied to clipboard:\n{selected_text}")
            else:
                messagebox.showwarning("Warning", "Please select a line to copy")
        
        copy_button = ttk.Button(button_frame, text="Copy Selected Line", command=copy_selected_line)
        copy_button.grid(row=0, column=0, padx=(0, 5))
        
        # Copy all data button
        def copy_all_data():
            all_text = "\n".join([listbox.get(i) for i in range(listbox.size())])
            popup.clipboard_clear()
            popup.clipboard_append(all_text)
            messagebox.showinfo("Copied", "All record data copied to clipboard")
        
        copy_all_button = ttk.Button(button_frame, text="Copy All Data", command=copy_all_data)
        copy_all_button.grid(row=0, column=1, padx=5)
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=popup.destroy)
        close_button.grid(row=0, column=2, padx=(5, 0))
        
        # Modified double-click handler for listbox
        def on_listbox_double_click(event):
            selection = listbox.curselection()
            if selection:
                selected_text = listbox.get(selection[0])
                # Check if the selected line is a Prompt File Path
                if selected_text.startswith("Prompt File Path:"):
                    # Extract the file path from the line
                    file_path = selected_text.split("Prompt File Path:", 1)[1].strip()
                    if file_path and file_path != "Unknown" and file_path != "No prompt files":
                        # Open the file in notepad-like window
                        self.open_file_in_notepad(file_path)
                    else:
                        messagebox.showwarning("Warning", "No valid file path found")
                else:
                    # For other lines, just copy them
                    copy_selected_line()
        
        listbox.bind('<Double-1>', on_listbox_double_click)
        
        # Bind Escape key to close popup
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        # Focus on the listbox
        listbox.focus_set()
    
    def find_latest_subfolder(self):
        """Find the latest date_extraction_output_* subfolder"""
        try:
            # Look for date_extraction_output_* folders in current directory
            pattern = "date_extraction_output_*"
            folders = glob.glob(pattern)
            
            if not folders:
                return None
            
            # Filter to only include directories
            folders = [f for f in folders if os.path.isdir(f)]
            
            if not folders:
                return None
            
            # Sort by modification time to get the latest
            latest_folder = max(folders, key=os.path.getmtime)
            return latest_folder
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding latest subfolder: {str(e)}")
            return None
    
    def find_comprehensive_summary_file(self, folder_path):
        """Find comprehensive_summary_*.json file in the given folder"""
        try:
            # Look for comprehensive_summary_*.json files in the folder
            pattern = os.path.join(folder_path, "comprehensive_summary_*.json")
            json_files = glob.glob(pattern)
            
            if not json_files:
                return None
            
            # Sort by modification time to get the latest
            latest_file = max(json_files, key=os.path.getmtime)
            return latest_file
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding comprehensive summary file: {str(e)}")
            return None
    
    def extract_file_details(self, json_data):
        """Extract file details from the JSON data"""
        file_details_list = []
        
        try:
            # Check if json_data has file_details array
            if isinstance(json_data, dict) and 'file_details' in json_data:
                file_details = json_data['file_details']
            elif isinstance(json_data, list):
                # If it's a list, look for file_details in each item
                file_details = []
                for item in json_data:
                    if isinstance(item, dict) and 'file_details' in item:
                        file_details.extend(item['file_details'])
            else:
                return []
            
            # Process each file detail
            for file_detail in file_details:
                scrap_file_name = file_detail.get('scrap_file_name', 'Unknown')
                scrap_file_location = file_detail.get('scrap_file_location', 'Unknown')
                source_url = file_detail.get('source_url', 'Unknown')
                
                # Handle prompt_files array
                prompt_files = file_detail.get('prompt_files', [])
                
                if prompt_files:
                    # Create a row for each prompt file
                    for prompt_file in prompt_files:
                        row = {
                            'scrap_file_name': scrap_file_name,
                            'scrap_file_location': scrap_file_location,
                            'source_url': source_url,
                            'prompt_file_name': prompt_file.get('prompt_file_name', 'Unknown'),
                            'prompt_file_path': prompt_file.get('prompt_file_path', 'Unknown'),
                            'batch_number': prompt_file.get('batch_number', 'Unknown')
                        }
                        file_details_list.append(row)
                else:
                    # Create a row even if no prompt files
                    row = {
                        'scrap_file_name': scrap_file_name,
                        'scrap_file_location': scrap_file_location,
                        'source_url': source_url,
                        'prompt_file_name': 'No prompt files',
                        'prompt_file_path': 'No prompt files',
                        'batch_number': 'N/A'
                    }
                    file_details_list.append(row)
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting file details: {str(e)}")
        
        return file_details_list
    
    def load_latest_results(self):
        """Load and display results from the latest comprehensive summary JSON file"""
        try:
            # Find the latest subfolder
            latest_folder = self.find_latest_subfolder()
            
            if not latest_folder:
                self.results_info_var.set("No date_extraction_output folder found")
                self.clear_results_table()
                self.download_button.config(state='disabled')
                return
            
            # Find comprehensive summary file in the folder
            self.latest_json_file = self.find_comprehensive_summary_file(latest_folder)
            
            if not self.latest_json_file:
                self.results_info_var.set(f"No comprehensive_summary file found in {latest_folder}")
                self.clear_results_table()
                self.download_button.config(state='disabled')
                return
            
            # Load JSON data
            with open(self.latest_json_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            
            # Extract file details from the JSON
            self.results_data = self.extract_file_details(self.raw_data)
            
            # Update display
            self.display_results()
            
            # Update info label
            file_time = datetime.fromtimestamp(os.path.getmtime(self.latest_json_file))
            self.results_info_var.set(
                f"File Details: {len(self.results_data)} items | "
                f"File: {os.path.basename(self.latest_json_file)} | "
                f"Modified: {file_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Enable download button
            self.download_button.config(state='normal')
            
            if self.logger:
                self.logger.info(f"Loaded file details from {self.latest_json_file}")
                
        except Exception as e:
            error_msg = f"Error loading results: {str(e)}"
            self.results_info_var.set("Error loading results")
            self.clear_results_table()
            self.download_button.config(state='disabled')
            
            if self.logger:
                self.logger.error(error_msg)
            else:
                messagebox.showerror("Error", error_msg)
    
    def display_results(self):
        """Display results in the table"""
        # Clear existing data
        self.clear_results_table()
        
        if not self.results_data:
            return
        
        # Populate table with file details
        for item in self.results_data:
            scrap_file_name = item.get('scrap_file_name', 'Unknown')
            scrap_file_location = item.get('scrap_file_location', 'Unknown')
            source_url = item.get('source_url', 'Unknown')
            prompt_file_name = item.get('prompt_file_name', 'Unknown')
            prompt_file_path = item.get('prompt_file_path', 'Unknown')
            batch_number = item.get('batch_number', 'Unknown')
            
            # Insert row with file details
            self.results_tree.insert('', tk.END, values=(
                scrap_file_name, scrap_file_location, source_url, 
                prompt_file_name, prompt_file_path, batch_number
            ))
    
    def clear_results_table(self):
        """Clear all items from the results table"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def download_csv(self):
        """Download results as CSV file"""
        try:
            if not self.results_data or not self.latest_json_file:
                messagebox.showwarning("Warning", "No data to download")
                return
            
            # Create DataFrame from results data
            df_data = []
            for item in self.results_data:
                row = {
                    'Scrap File Name': item.get('scrap_file_name', 'Unknown'),
                    'Scrap File Location': item.get('scrap_file_location', 'Unknown'),
                    'Source URL': item.get('source_url', 'Unknown'),
                    'Prompt File Name': item.get('prompt_file_name', 'Unknown'),
                    'Prompt File Path': item.get('prompt_file_path', 'Unknown'),
                    'Batch Number': item.get('batch_number', 'Unknown')
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Generate CSV filename based on JSON filename
            json_basename = os.path.splitext(os.path.basename(self.latest_json_file))[0]
            csv_filename = f"{json_basename}_file_details.csv"
            
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=csv_filename,
                title="Save CSV File"
            )
            
            if file_path:
                # Save CSV
                df.to_csv(file_path, index=False, encoding='utf-8')
                
                messagebox.showinfo(
                    "Success", 
                    f"File details exported successfully to:\n{file_path}\n\n"
                    f"Total records: {len(df_data)}"
                )
                
                if self.logger:
                    self.logger.info(f"File details exported to CSV: {file_path}")
            
        except Exception as e:
            error_msg = f"Error downloading CSV: {str(e)}"
            messagebox.showerror("Error", error_msg)
            
            if self.logger:
                self.logger.error(error_msg)
    
    def on_scraping_complete(self):
        """Called when scraping is complete or cancelled"""
        # Automatically load the latest results
        self.load_latest_results()
    
    def get_frame_width(self):
        """Get the recommended width for the results frame"""
        return 900  # Increased width to accommodate more columns