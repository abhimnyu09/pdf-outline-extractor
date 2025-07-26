#!/usr/bin/env python3
"""
Enhanced Multilingual PDF Outline Extractor
Supports Japanese, German, French, Chinese, Arabic, and many other languages
"""

import os
import json
import sys
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not found. Installing...")
    os.system("pip install PyMuPDF")
    import fitz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultilingualPDFOutlineExtractor:
    def __init__(self):
        # Multilingual heading patterns
        self.heading_patterns = {
            'numbered': [
                r'^(?:\d+\.?\s*)+[^\d].*$',  # 1., 1.1, 1.1.1 etc
                r'^(?:[IVX]+\.?\s*)+.*$',    # Roman numerals
                r'^(?:[A-Z]\.?\s*)+.*$',     # A., B., C. etc
                r'^(?:\([0-9]+\)\s*).*$',    # (1), (2) etc
                r'^(?:\[[0-9]+\]\s*).*$',    # [1], [2] etc
            ],
            'chapter_section': [
                # English
                r'^(?:Chapter|Section|Part)\s+(?:\d+|[IVX]+)',
                # German
                r'^(?:Kapitel|Abschnitt|Teil)\s+(?:\d+|[IVX]+)',
                # French  
                r'^(?:Chapitre|Section|Partie)\s+(?:\d+|[IVX]+)',
                # Spanish
                r'^(?:Capítulo|Sección|Parte)\s+(?:\d+|[IVX]+)',
                # Italian
                r'^(?:Capitolo|Sezione|Parte)\s+(?:\d+|[IVX]+)',
                # Portuguese
                r'^(?:Capítulo|Seção|Parte)\s+(?:\d+|[IVX]+)',
                # Japanese (using numbers)
                r'^(?:第\d+章|第\d+節|第\d+部)',
                # Chinese
                r'^(?:第[一二三四五六七八九十\d]+章|第[一二三四五六七八九十\d]+节)',
            ],
            'all_caps': [
                r'^[A-Z\u00C0-\u017F\u0400-\u04FF]{3,}(?:\s+[A-Z\u00C0-\u017F\u0400-\u04FF]{3,})*\s*$',  # Latin + Cyrillic
                r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{3,}\s*$',  # Japanese/Chinese
            ],
            'title_case': [
                r'^[A-Z\u00C0-\u017F][a-z\u00C0-\u017F\u0400-\u04FF\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF].{2,}$',
            ]
        }
        
        # Common non-heading words in various languages
        self.non_heading_words = {
            'english': ['abstract', 'introduction', 'contents', 'table of contents', 'references', 'bibliography'],
            'german': ['zusammenfassung', 'einleitung', 'inhaltsverzeichnis', 'literatur', 'bibliographie'],
            'french': ['résumé', 'introduction', 'table des matières', 'références', 'bibliographie'],
            'spanish': ['resumen', 'introducción', 'índice', 'referencias', 'bibliografía'],
            'japanese': ['要約', '概要', '目次', '参考文献'],
            'chinese': ['摘要', '简介', '目录', '参考文献'],
            'arabic': ['ملخص', 'مقدمة', 'فهرس', 'مراجع'],
        }
    
    def detect_language(self, text_blocks: List[Dict]) -> str:
        """Detect the primary language of the document"""
        # Sample text from first few pages
        sample_text = ' '.join([block['text'] for block in text_blocks[:50] if block['page'] <= 3])
        
        # Simple language detection based on character ranges
        char_counts = {
            'latin': 0,
            'cyrillic': 0, 
            'cjk': 0,  # Chinese, Japanese, Korean
            'arabic': 0,
        }
        
        for char in sample_text:
            if '\u0020' <= char <= '\u024F':  # Latin scripts
                char_counts['latin'] += 1
            elif '\u0400' <= char <= '\u04FF':  # Cyrillic
                char_counts['cyrillic'] += 1
            elif '\u3040' <= char <= '\u9FAF':  # CJK
                char_counts['cjk'] += 1
            elif '\u0600' <= char <= '\u06FF':  # Arabic
                char_counts['arabic'] += 1
        
        # Return dominant script
        return max(char_counts, key=char_counts.get)
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for better comparison"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize Unicode (important for multilingual text)
        text = unicodedata.normalize('NFKC', text)
        
        return text
    
    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        """Extract text with formatting information from PDF"""
        doc = fitz.open(pdf_path)
        text_blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = self.normalize_text(span["text"])
                            if text:
                                text_blocks.append({
                                    "text": text,
                                    "page": page_num + 1,
                                    "font_size": span["size"],
                                    "font_flags": span["flags"],
                                    "font_name": span["font"],
                                    "bbox": span["bbox"]
                                })
        
        doc.close()
        return text_blocks
    
    def is_bold(self, font_flags: int) -> bool:
        """Check if text is bold based on font flags"""
        return bool(font_flags & 2**4)
    
    def matches_heading_pattern(self, text: str, language: str) -> Tuple[bool, str]:
        """Check if text matches any heading pattern"""
        # Check numbered patterns (language-agnostic)
        for pattern in self.heading_patterns['numbered']:
            if re.match(pattern, text, re.IGNORECASE):
                return True, 'numbered'
        
        # Check chapter/section patterns
        for pattern in self.heading_patterns['chapter_section']:
            if re.match(pattern, text, re.IGNORECASE):
                return True, 'chapter_section'
        
        # Check ALL CAPS patterns
        for pattern in self.heading_patterns['all_caps']:
            if re.match(pattern, text):
                return True, 'all_caps'
        
        # Check title case patterns
        for pattern in self.heading_patterns['title_case']:
            if re.match(pattern, text):
                return True, 'title_case'
        
        return False, 'none'
    
    def is_likely_non_heading(self, text: str) -> bool:
        """Check if text is likely not a heading"""
        text_lower = text.lower()
        
        # Check against non-heading words in all languages
        for lang_words in self.non_heading_words.values():
            if any(word in text_lower for word in lang_words):
                return True
        
        # Skip very short or very long text
        if len(text) < 3 or len(text) > 200:
            return True
        
        # Skip pure numbers or dates
        if re.match(r'^[\d\s\-\/\.]+$', text):
            return True
        
        return False
    
    def classify_heading_level(self, text: str, font_size: float, is_bold: bool, 
                             avg_font_size: float, max_font_size: float, language: str) -> Optional[str]:
        """Classify text as H1, H2, H3 or None based on various criteria"""
        
        # Skip likely non-headings
        if self.is_likely_non_heading(text):
            return None
        
        # Check if text matches heading patterns
        is_heading_pattern, pattern_type = self.matches_heading_pattern(text, language)
        
        # Font size based classification
        font_size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1
        
        # Scoring system
        score = 0
        
        # Pattern matching scores
        if pattern_type == 'numbered':
            score += 4
        elif pattern_type == 'chapter_section':
            score += 5
        elif pattern_type == 'all_caps':
            score += 3
        elif pattern_type == 'title_case':
            score += 2
        
        # Font size scores
        if font_size_ratio > 1.8:
            score += 4
        elif font_size_ratio > 1.5:
            score += 3
        elif font_size_ratio > 1.2:
            score += 2
        elif font_size_ratio > 1.1:
            score += 1
        
        # Bold formatting score
        if is_bold:
            score += 2
        
        # Specific numbered heading level detection
        if re.match(r'^\d+\.\s+', text):
            return "H1"
        elif re.match(r'^\d+\.\d+\s+', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            return "H3"
        
        # Chapter/Section detection
        if pattern_type == 'chapter_section':
            return "H1"
        
        # Score-based classification
        if score >= 6:
            return "H1"
        elif score >= 4:
            return "H2"
        elif score >= 3:
            return "H3"
        
        return None
    
    def extract_title(self, text_blocks: List[Dict], language: str) -> str:
        """Extract document title from text blocks"""
        # Look for title in first few pages
        first_page_blocks = [block for block in text_blocks if block["page"] <= 2]
        
        if not first_page_blocks:
            return "Untitled Document"
        
        # Sort by font size (largest first) and position
        first_page_blocks.sort(key=lambda x: (-x["font_size"], x["bbox"][1]))
        
        # Find the largest, most prominent text as title
        for block in first_page_blocks[:15]:
            text = block["text"].strip()
            
            # Skip if it's likely not a title
            if self.is_likely_non_heading(text):
                continue
            
            # Skip if it starts with common non-title patterns
            if re.match(r'^(?:Page|页|頁|\d+)(?:\s|$)', text, re.IGNORECASE):
                continue
            
            # Check if it looks like a title
            if (len(text) > 5 and len(text) < 150 and
                not re.match(r'^\d+\.', text)):  # Not a numbered heading
                return text
        
        # Fallback to first substantial text
        for block in first_page_blocks:
            text = block["text"].strip()
            if len(text) > 10 and len(text) < 100:
                return text
        
        return "Untitled Document"
    
    def extract_outline(self, pdf_path: str) -> Dict:
        """Extract outline from PDF"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        text_blocks = self.extract_text_with_formatting(pdf_path)
        
        if not text_blocks:
            logger.warning(f"No text found in {pdf_path}")
            return {"title": "Untitled Document", "outline": []}
        
        # Detect document language
        language = self.detect_language(text_blocks)
        logger.info(f"Detected language script: {language}")
        
        # Calculate font statistics
        font_sizes = [block["font_size"] for block in text_blocks]
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        max_font_size = max(font_sizes) if font_sizes else 12
        
        # Extract title
        title = self.extract_title(text_blocks, language)
        
        # Extract headings
        outline = []
        seen_headings = set()
        
        for block in text_blocks:
            text = block["text"].strip()
            
            # Skip duplicates or empty text
            if text in seen_headings or not text:
                continue
            
            font_size = block["font_size"]
            is_bold = self.is_bold(block["font_flags"])
            
            # Classify heading level
            level = self.classify_heading_level(
                text, font_size, is_bold, avg_font_size, max_font_size, language
            )
            
            if level:
                outline.append({
                    "level": level,
                    "text": text,
                    "page": block["page"]
                })
                seen_headings.add(text)
        
        # Sort by page number and level
        outline = sorted(outline, key=lambda x: (x["page"], x["level"]))
        
        # Limit to reasonable number of headings
        if len(outline) > 100:
            outline = outline[:100]
        
        logger.info(f"Extracted {len(outline)} headings from {pdf_path}")
        
        return {
            "title": title,
            "outline": outline
        }

def process_pdfs(input_dir: str, output_dir: str):
    """Process all PDFs in input directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return
    
    extractor = MultilingualPDFOutlineExtractor()
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}")
            
            # Extract outline
            result = extractor.extract_outline(str(pdf_file))
            
            # Save to JSON with proper UTF-8 encoding
            output_file = output_path / f"{pdf_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved outline to {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            # Create empty result on error
            error_result = {"title": "Error Processing Document", "outline": []}
            output_file = output_path / f"{pdf_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)

def main():
    """Main function"""
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Check if directories exist
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist")
        sys.exit(1)
    
    logger.info("Starting multilingual PDF outline extraction")
    process_pdfs(input_dir, output_dir)
    logger.info("PDF outline extraction completed")

if __name__ == "__main__":
    main()
