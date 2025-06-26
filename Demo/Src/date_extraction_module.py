#!/usr/bin/env python3
"""
Date Extraction Module - Modular implementation for date extraction from scraped files
Can be used as a standalone script or imported as a module
Modified to include URL extraction, CSV output format, and comprehensive summaries
"""

import os
import re
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone

# Check if tiktoken is available, if not provide fallback
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class DateExtractorBase:
    """Base class for date extraction functionality"""
    
    def __init__(self, max_tokens: int = 3500, output_prefix: str = "date_extraction_output"):
        self.max_tokens = max_tokens
        self.output_prefix = output_prefix
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"{output_prefix}_{self.timestamp}")
        
        # Initialize tokenizer
        if TIKTOKEN_AVAILABLE:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.count_tokens = lambda text: len(self.tokenizer.encode(text))
        else:
            print("⚠️  tiktoken not installed - using approximate token counting")
            print("   Install with: pip install tiktoken")
            self.count_tokens = self._count_tokens_fallback
        
        # Comprehensive date patterns
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{2,4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b',
            r'\bQ[1-4]\s+\d{4}\b',  # Q1 2024
            r'\b(FY|CY)\s*\d{2,4}\b',  # FY2024
            r'\b20\d{2}\b',  # Years 2000-2099
            r'\b\d{4}-\d{2}-\d{2}T?\d{0,2}:?\d{0,2}:?\d{0,2}\b',  # ISO dates
            r'\b(early|mid|late)\s+(20\d{2})\b',
            r'\b(spring|summer|fall|winter|autumn)\s+(20\d{2})\b',
            r'\b(end\s+of|by\s+end\s+of)\s+\w+\s+\d{4}\b'
        ]
        
        self.results = []
        self.no_dates_files = []
        self.file_summary_data = []  # For comprehensive summary
    
    def _count_tokens_fallback(self, text: str) -> int:
        """Fallback token counter when tiktoken is not available"""
        return len(text) // 4
    
    def extract_url_from_file(self, filepath: Path) -> Optional[str]:
        """Extract URL from scrap file - typically found at the beginning"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to look for URL
                for i, line in enumerate(f):
                    if i > 10:  # Only check first 10 lines
                        break
                    # Look for URL patterns
                    url_match = re.search(r'https?://[^\s<>"\']+', line)
                    if url_match:
                        return url_match.group(0)
                    # Also check for common URL indicators
                    if 'URL:' in line or 'Source:' in line:
                        url_match = re.search(r'https?://[^\s<>"\']+', line)
                        if url_match:
                            return url_match.group(0)
            return None
        except Exception as e:
            print(f"Error extracting URL from {filepath}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-/.:,;()]+', ' ', text)
        return text.strip()
    
    def extract_context(self, text: str, start: int, end: int, words: int = 100) -> str:
        """Extract context around found date"""
        text_words = text.split()
        char_pos = 0
        word_start = 0
        for i, word in enumerate(text_words):
            if char_pos >= start:
                word_start = max(0, i - words)
                word_end = min(len(text_words), i + words)
                return ' '.join(text_words[word_start:word_end])
            char_pos += len(word) + 1
        return text[:500]  # Fallback
    
    def find_dates(self, text: str, filename: str, url: Optional[str] = None) -> List[Dict]:
        """Find all dates in text"""
        dates_found = []
        found_positions = set()
        clean_text = self.clean_text(text)
        
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, clean_text, re.IGNORECASE):
                if any(abs(match.start() - pos) < 10 for pos in found_positions):
                    continue
                
                found_positions.add(match.start())
                context = self.extract_context(clean_text, match.start(), match.end())
                
                dates_found.append({
                    'filename': filename,
                    'date': match.group(0),
                    'context': context,
                    'position': match.start(),
                    'url': url or 'Not available'
                })
        
        return dates_found
    
    def create_output_directory(self) -> None:
        """Create output directory"""
        self.output_dir.mkdir(exist_ok=True)
    
    def find_scrap_files(self, directory: Optional[Path] = None) -> List[Path]:
        """Find all files starting with 'Scrap_' and ending with '.txt'"""
        search_dir = directory or Path(".")
        return list(search_dir.glob("Scrap_*.txt"))


class SimpleDateExtractor(DateExtractorBase):
    """Simple date extractor implementation (based on run_date_extraction.py)"""
    
    def __init__(self, max_tokens: int = 3000):
        super().__init__(max_tokens, "date_extraction_output")
    
    def create_prompt(self, dates: List[Dict]) -> str:
        """Create LLM prompt with URL information and CSV output format"""
        # Group by file
        by_file = {}
        for d in dates:
            if d['filename'] not in by_file:
                by_file[d['filename']] = []
            by_file[d['filename']].append(d)
        
        # Build context with URL information
        sections = []
        for filename, file_dates in by_file.items():
            # Get URL from first date entry (all dates from same file have same URL)
            file_url = file_dates[0]['url'] if file_dates else 'Not available'
            sections.append(f"=== FILE: {filename} ===")
            sections.append(f"URL: {file_url}")
            sections.append("")
            for date_info in file_dates:
                sections.append(f"Date: {date_info['date']}")
                sections.append(f"Context: {date_info['context']}")
                sections.append("---")
        
        context_text = "\n".join(sections)
        
        return f"""Analyze the text below and identify business-critical dates. Look for dates related to:

1. End of Life (EOL) - Product manufacturing stops
2. End of Sales (EOS) - Last purchase date
3. End of Service/Support - Support ends
4. End of Security Updates - Security patches stop
5. Last Order Date - Final ordering deadline
6. Retirement/Discontinuation - Product retirement
7. Migration Deadline - Must migrate by this date
8. Contract/License Expiration - Agreements expire
9. Other Business Critical Dates

TEXT TO ANALYZE:
{context_text}

For each business-relevant date found, provide:
- Product/service name (if mentioned)
- Exact date
- Category (from list above)
- Context quote
- URL (from the source file)
- Confidence (High/Medium/Low)

Ignore: publication dates, random timestamps, non-business dates

RESPOND IN CSV FORMAT:
"product","date","category","context","url","confidence"

Provide only the CSV data rows, no headers or additional text."""
    
    def process_files(self, file_paths: Optional[List[Path]] = None) -> Tuple[List[Dict], List[str]]:
        """Process files and extract dates with URL information"""
        if file_paths is None:
            file_paths = self.find_scrap_files()
        
        all_dates = []
        no_date_files = []
        
        for file_path in file_paths:
            try:
                # Extract URL from file
                url = self.extract_url_from_file(file_path)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                dates = self.find_dates(content, file_path.name, url)
                if dates:
                    all_dates.extend(dates)
                    # Store summary data
                    self.file_summary_data.append({
                        'scrap_file_name': file_path.name,
                        'scrap_file_path': str(file_path.absolute()),
                        'url': url or 'Not available',
                        'dates_found': len(dates),
                        'has_dates': True
                    })
                else:
                    no_date_files.append(file_path.name)
                    self.file_summary_data.append({
                        'scrap_file_name': file_path.name,
                        'scrap_file_path': str(file_path.absolute()),
                        'url': url or 'Not available',
                        'dates_found': 0,
                        'has_dates': False
                    })
            
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")
                no_date_files.append(file_path.name)
                self.file_summary_data.append({
                    'scrap_file_name': file_path.name,
                    'scrap_file_path': str(file_path.absolute()),
                    'url': 'Error extracting',
                    'dates_found': 0,
                    'has_dates': False,
                    'error': str(e)
                })
        
        return all_dates, no_date_files
    
    def create_batches(self, dates: List[Dict]) -> List[List[Dict]]:
        """Create batches from dates"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for date_info in dates:
            tokens = self.count_tokens(date_info['context'])
            
            if current_tokens + tokens > self.max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [date_info]
                current_tokens = tokens
            else:
                current_batch.append(date_info)
                current_tokens += tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def generate_prompt_files(self, batches: List[List[Dict]]) -> List[str]:
        """Generate prompt files from batches"""
        self.create_output_directory()
        prompt_files = []
        
        for i, batch in enumerate(batches):
            prompt = self.create_prompt(batch)
            filename = f"prompt_{self.timestamp}_batch_{i+1}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            prompt_files.append(filename)
            
            # Update summary data with prompt file information
            batch_files = set(d['filename'] for d in batch)
            for summary_item in self.file_summary_data:
                if summary_item['scrap_file_name'] in batch_files:
                    if 'prompt_files' not in summary_item:
                        summary_item['prompt_files'] = []
                    summary_item['prompt_files'].append({
                        'prompt_file_name': filename,
                        'prompt_file_path': str(filepath.absolute()),
                        'batch_number': i + 1
                    })
        
        return prompt_files
    
    def save_summary(self, files_processed: List[str], total_dates: int, 
                    no_date_files: List[str], prompt_files: List[str]) -> None:
        """Save processing summary"""
        summary = {
            'timestamp': self.timestamp,
            'files_processed': files_processed,
            'total_dates_found': total_dates,
            'files_with_dates': len(files_processed) - len(no_date_files),
            'files_without_dates': no_date_files,
            'prompt_batches': len(prompt_files),
            'prompt_files': prompt_files
        }
        
        with open(self.output_dir / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def save_comprehensive_summary(self) -> None:
        """Save comprehensive summary JSON file with all details"""
        comprehensive_summary = {
            'processing_timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'extraction_session_id': self.timestamp,
            'output_directory': str(self.output_dir.absolute()),
            'total_files_processed': len(self.file_summary_data),
            'files_with_dates': len([f for f in self.file_summary_data if f['has_dates']]),
            'files_without_dates': len([f for f in self.file_summary_data if not f['has_dates']]),
            'total_dates_found': sum(f['dates_found'] for f in self.file_summary_data),
            'file_details': []
        }
        
        for file_data in self.file_summary_data:
            file_detail = {
                'scrap_file_name': file_data['scrap_file_name'],
                'scrap_file_location': file_data['scrap_file_path'],
                'source_url': file_data['url'],
                'dates_found_count': file_data['dates_found'],
                'has_business_dates': file_data['has_dates'],
                'prompt_files': file_data.get('prompt_files', [])
            }
            
            if 'error' in file_data:
                file_detail['processing_error'] = file_data['error']
            
            comprehensive_summary['file_details'].append(file_detail)
        
        summary_filename = f"comprehensive_summary_{self.timestamp}.json"
        with open(self.output_dir / summary_filename, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_summary, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Comprehensive summary saved: {summary_filename}")
    
    def run(self, directory: Optional[Path] = None, verbose: bool = True) -> Dict:
        """Main execution method"""
        if verbose:
            print("🔍 Looking for Scrap_*.txt files...")
        
        scrap_files = self.find_scrap_files(directory)
        
        if not scrap_files:
            if verbose:
                print("❌ No Scrap_*.txt files found")
            return {'success': False, 'message': 'No files found'}
        
        if verbose:
            print(f"📁 Found {len(scrap_files)} files")
        
        # Process files
        all_dates, no_date_files = self.process_files(scrap_files)
        
        if not all_dates:
            if verbose:
                print("❌ No dates found in any files!")
            # Still save comprehensive summary even if no dates found
            self.save_comprehensive_summary()
            return {'success': False, 'message': 'No dates found'}
        
        if verbose:
            print(f"📊 Total dates found: {len(all_dates)}")
        
        # Create batches and generate files
        batches = self.create_batches(all_dates)
        prompt_files = self.generate_prompt_files(batches)
        
        # Save summaries
        self.save_summary([f.name for f in scrap_files], len(all_dates), 
                         no_date_files, prompt_files)
        self.save_comprehensive_summary()
        
        if verbose:
            print(f"✅ Generated {len(prompt_files)} prompt files in {self.output_dir}")
        
        return {
            'success': True,
            'output_directory': str(self.output_dir),
            'prompt_files': prompt_files,
            'total_dates': len(all_dates),
            'files_processed': len(scrap_files)
        }


class DateExtractionPipeline(DateExtractorBase):
    """Advanced date extraction pipeline (based on date_extraction_script.py)"""
    
    def __init__(self, max_tokens: int = 3500):
        super().__init__(max_tokens, "date_extraction_output")
    
    def split_into_chunks(self, text: str, max_chunk_tokens: int = 2000) -> List[str]:
        """Split large text into manageable chunks"""
        if self.count_tokens(text) <= max_chunk_tokens:
            return [text]
        
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            if self.count_tokens(test_chunk) > max_chunk_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_file(self, filepath: Path, verbose: bool = True) -> bool:
        """Process a single file"""
        try:
            if verbose:
                print(f"  Processing: {filepath.name}")
            
            # Extract URL from file
            url = self.extract_url_from_file(filepath)
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            chunks = self.split_into_chunks(content)
            file_has_dates = False
            dates_count = 0
            
            for i, chunk in enumerate(chunks):
                chunk_name = f"{filepath.name}_chunk_{i+1}" if len(chunks) > 1 else filepath.name
                matches = self.find_dates_in_text(chunk, chunk_name, url)
                if matches:
                    file_has_dates = True
                    dates_count += len(matches)
                    self.results.extend(matches)
                    if verbose:
                        print(f"    Found {len(matches)} dates in {'chunk ' + str(i+1) if len(chunks) > 1 else 'file'}")
            
            # Store summary data
            self.file_summary_data.append({
                'scrap_file_name': filepath.name,
                'scrap_file_path': str(filepath.absolute()),
                'url': url or 'Not available',
                'dates_found': dates_count,
                'has_dates': file_has_dates
            })
            
            if not file_has_dates:
                self.no_dates_files.append(str(filepath))
                if verbose:
                    print(f"    No dates found in {filepath.name}")
            
            return file_has_dates
                
        except Exception as e:
            if verbose:
                print(f"    ERROR processing {filepath}: {e}")
            # Store error in summary data
            self.file_summary_data.append({
                'scrap_file_name': filepath.name,
                'scrap_file_path': str(filepath.absolute()),
                'url': 'Error extracting',
                'dates_found': 0,
                'has_dates': False,
                'error': str(e)
            })
            return False
    
    def find_dates_in_text(self, text: str, filename: str, url: Optional[str] = None) -> List[Dict]:
        """Find ALL date patterns in text"""
        matches = []
        clean_text = self.clean_text(text)
        found_positions = set()
        
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, clean_text, re.IGNORECASE):
                if any(abs(match.start() - pos) < 10 for pos in found_positions):
                    continue
                    
                found_positions.add(match.start())
                context = self.extract_context(clean_text, match.start(), match.end())
                
                matches.append({
                    'filename': filename,
                    'date_found': match.group(0),
                    'context': context,
                    'position': match.start(),
                    'pattern_used': pattern,
                    'url': url or 'Not available'
                })
        
        return matches
    
    def create_prompt_template(self, matches: List[Dict]) -> str:
        """Create comprehensive prompt for LLM analysis with CSV output"""
        contexts_by_file = {}
        for match in matches:
            filename = match['filename']
            if filename not in contexts_by_file:
                contexts_by_file[filename] = {
                    'url': match['url'],
                    'matches': []
                }
            contexts_by_file[filename]['matches'].append({
                'date': match['date_found'],
                'context': match['context']
            })
        
        context_sections = []
        for filename, file_data in contexts_by_file.items():
            context_sections.append(f"=== SOURCE: {filename} ===")
            context_sections.append(f"URL: {file_data['url']}")
            context_sections.append("")
            for match in file_data['matches']:
                context_sections.append(f"Date Found: {match['date']}")
                context_sections.append(f"Context: {match['context']}")
                context_sections.append("---")
        
        context_text = "\n".join(context_sections)
        
        return f"""You are analyzing text from web scraping to identify business-critical dates. Below are text snippets containing various dates. Your task is to identify and categorize dates that relate to product lifecycle, support, or business operations.

TEXT TO ANALYZE:
{context_text}

TASK: Analyze each date found and determine if it relates to any of these categories:
1. End of Life (EOL) - When product stops being manufactured
2. End of Sales (EOS) - Last date for purchasing  
3. End of Service/Support - When support/service ends
4. End of Security Updates - When security patches stop
5. Last Order Date - Final date to place orders
6. Retirement/Discontinuation Date - When product is retired
7. Migration Deadline - When users must migrate to new solution
8. Contract Expiration - When agreements/licenses expire
9. Other Business Critical Dates - Any other important business dates

For each relevant date you identify, provide:
- Product/service name if mentioned
- The exact date
- Category (from list above)
- Source context (brief quote showing how date was mentioned)
- URL (from the source file)
- Confidence level (High/Medium/Low)

IMPORTANT: 
- Only include dates that appear to be business/product related
- Ignore random dates, publication dates, or irrelevant timestamps
- If a date's purpose is unclear, mark confidence as "Low"
- If no relevant dates are found, respond with a single row: "No business-critical dates identified","","","","",""

RESPOND IN CSV FORMAT:
"product","date","category","context","url","confidence"

Provide only the CSV data rows, no headers or additional text."""
    
    def group_into_batches(self) -> List[List[Dict]]:
        """Group matches into token-appropriate batches"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        sorted_results = sorted(self.results, key=lambda x: x['filename'])
        
        for match in sorted_results:
            match_tokens = self.count_tokens(match['context'])
            
            if current_tokens + match_tokens > self.max_tokens - 800:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = [match]
                    current_tokens = match_tokens
                else:
                    chunks = self.split_into_chunks(match['context'], 1500)
                    for chunk in chunks:
                        batches.append([{**match, 'context': chunk}])
            else:
                current_batch.append(match)
                current_tokens += match_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def generate_output_files(self, batches: List[List[Dict]]) -> List[str]:
        """Generate prompt and metadata files"""
        self.create_output_directory()
        prompt_files = []
        
        for i, batch in enumerate(batches):
            prompt = self.create_prompt_template(batch)
            
            prompt_filename = f"prompt_{self.timestamp}_batch_{i+1}.txt"
            prompt_path = self.output_dir / prompt_filename
            
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            prompt_files.append(prompt_filename)
            
            # Update summary data with prompt file information
            batch_files = set(d['filename'].split('_chunk_')[0] if '_chunk_' in d['filename'] else d['filename'] for d in batch)
            for summary_item in self.file_summary_data:
                if summary_item['scrap_file_name'] in batch_files:
                    if 'prompt_files' not in summary_item:
                        summary_item['prompt_files'] = []
                    summary_item['prompt_files'].append({
                        'prompt_file_name': prompt_filename,
                        'prompt_file_path': str(prompt_path.absolute()),
                        'batch_number': i + 1
                    })
            
            # Save batch metadata
            metadata_filename = f"batch_{i+1}_metadata.json"
            with open(self.output_dir / metadata_filename, 'w', encoding='utf-8') as f:
                json.dump(batch, f, indent=2, ensure_ascii=False)
        
        return prompt_files
    
    def save_comprehensive_summary(self, scrap_files: List[Path], prompt_files: List[str]) -> None:
        """Save comprehensive processing summary"""
        comprehensive_summary = {
            'processing_timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'extraction_session_id': self.timestamp,
            'output_directory': str(self.output_dir.absolute()),
            'total_files_processed': len(scrap_files),
            'files_with_dates': len(scrap_files) - len(self.no_dates_files),
            'files_without_dates': len(self.no_dates_files),
            'total_date_instances_found': len(self.results),
            'prompt_batches_created': len(prompt_files),
            'file_details': []
        }
        
        for file_data in self.file_summary_data:
            file_detail = {
                'scrap_file_name': file_data['scrap_file_name'],
                'scrap_file_location': file_data['scrap_file_path'],
                'source_url': file_data['url'],
                'dates_found_count': file_data['dates_found'],
                'has_business_dates': file_data['has_dates'],
                'prompt_files': file_data.get('prompt_files', [])
            }
            
            if 'error' in file_data:
                file_detail['processing_error'] = file_data['error']
            
            comprehensive_summary['file_details'].append(file_detail)
        
        # Save comprehensive summary
        summary_filename = f"comprehensive_summary_{self.timestamp}.json"
        with open(self.output_dir / summary_filename, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_summary, f, indent=2, ensure_ascii=False)
        
        # Also save the original extraction summary for backward compatibility
        original_summary = {
            'processing_timestamp': self.timestamp,
            'total_files_processed': len(scrap_files),
            'files_with_dates': len(scrap_files) - len(self.no_dates_files),
            'files_without_dates': len(self.no_dates_files),
            'total_date_instances_found': len(self.results),
            'prompt_batches_created': len(prompt_files),
            'files_processed': [f.name for f in scrap_files],
            'files_without_dates_list': self.no_dates_files,
            'output_directory': str(self.output_dir),
            'prompt_files_generated': prompt_files
        }
        
        with open(self.output_dir / "extraction_summary.json", 'w', encoding='utf-8') as f:
            json.dump(original_summary, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Comprehensive summary saved: {summary_filename}")
    
    def run_pipeline(self, directory: Optional[Path] = None, verbose: bool = True) -> Dict:
        """Run the complete extraction pipeline"""
        if verbose:
            print("=" * 60)
            print("STARTING DATE EXTRACTION PIPELINE")
            print("=" * 60)
        
        scrap_files = self.find_scrap_files(directory)
        
        if not scrap_files:
            if verbose:
                print("❌ No files found starting with 'Scrap_' and ending with '.txt'")
            return {'success': False, 'message': 'No scrap files found'}
        
        if verbose:
            print(f"📁 Found {len(scrap_files)} scrap files to process")
            print("🔍 Processing files for date extraction...")
        
        # Process all files - clear results first
        self.results = []
        self.no_dates_files = []
        self.file_summary_data = []
        
        for filepath in scrap_files:
            self.process_file(filepath, verbose)
        
        if verbose:
            print(f"\n📊 PROCESSING SUMMARY:")
            print(f"   • Total files processed: {len(scrap_files)}")
            print(f"   • Files with dates found: {len(scrap_files) - len(self.no_dates_files)}")
            print(f"   • Total date instances found: {len(self.results)}")
        
        if not self.results:
            if verbose:
                print("❌ No dates found in any files.")
            # Still save comprehensive summary even if no dates found
            self.save_comprehensive_summary(scrap_files, [])
            return {'success': False, 'message': 'No dates found'}
        
        # Group into batches and generate files
        batches = self.group_into_batches()
        prompt_files = self.generate_output_files(batches)
        self.save_comprehensive_summary(scrap_files, prompt_files)
        
        if verbose:
            print(f"\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"📁 Output directory: {self.output_dir}")
            print(f"📝 Generated {len(prompt_files)} prompt files")
        
        return {
            'success': True,
            'output_directory': str(self.output_dir),
            'prompt_files': prompt_files,
            'total_dates': len(self.results),
            'files_processed': len(scrap_files),
            'batches_created': len(batches)
        }


# Convenience functions for backward compatibility and easy usage
def run_simple_extraction(directory: Optional[Path] = None, verbose: bool = True) -> Dict:
    """Run simple date extraction (equivalent to run_date_extraction.py)"""
    extractor = SimpleDateExtractor()
    return extractor.run(directory, verbose)


def run_advanced_pipeline(directory: Optional[Path] = None, verbose: bool = True) -> Dict:
    """Run advanced date extraction pipeline (equivalent to date_extraction_script.py)"""
    pipeline = DateExtractionPipeline()
    return pipeline.run_pipeline(directory, verbose)


# Main execution for standalone use
if __name__ == "__main__":
    import sys
    
    print("🔧 Date Extraction Module - Enhanced with URL extraction and CSV output")
    print("Choose extraction method:")
    print("1. Simple extraction (faster, basic prompts)")
    print("2. Advanced pipeline (detailed analysis, comprehensive prompts)")
    
    choice = input("Enter choice (1 or 2, default=2): ").strip()
    
    if choice == "1":
        print("\n🚀 Running Simple Date Extraction...")
        result = run_simple_extraction()
    else:
        print("\n🚀 Running Advanced Date Extraction Pipeline...")
        result = run_advanced_pipeline()
    
    if result['success']:
        print(f"\n✨ Processing completed successfully!")
        print(f"📁 Check output directory: {result['output_directory']}")
        print(f"📋 Comprehensive summary with URLs and file details has been generated")
    else:
        print(f"\n❌ Processing failed: {result['message']}")
        sys.exit(1)
        