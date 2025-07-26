# PDF Outline Extractor

A robust solution for extracting structured outlines from PDF documents, designed for the hackathon challenge.

## Approach

This solution uses a multi-criteria approach to identify and classify headings in PDF documents:

### 1. Text Extraction with Formatting
- Uses PyMuPDF (fitz) to extract text with formatting information
- Captures font size, font flags (bold/italic), font name, and positioning data
- Processes all pages while maintaining page number information

### 2. Heading Detection Strategy
The solution employs multiple criteria for heading detection:

**Pattern Matching:**
- Numbered headings (1., 1.1, 1.1.1)
- ALL CAPS text
- Chapter/Section patterns
- Title case patterns

**Font-Based Analysis:**
- Font size relative to document average
- Bold text detection via font flags
- Font name analysis for heading fonts

**Scoring System:**
- Combines pattern matching, font size, and formatting
- Assigns confidence scores to classify H1, H2, H3 levels
- Uses thresholds to determine final heading levels

### 3. Title Extraction
- Analyzes first 1-2 pages for title candidates
- Prioritizes largest, most prominent text
- Filters out common non-title patterns
- Fallback mechanisms for edge cases

### 4. Multilingual Support
- Unicode-aware text processing
- No language-specific assumptions
- Handles various character encodings

## Libraries Used

- **PyMuPDF (fitz)**: PDF text extraction with formatting preservation
- **re**: Pattern matching for heading detection
- **json**: Output formatting
- **pathlib**: File system operations

## Model Information

No external ML models are used. The solution relies on:
- Rule-based pattern matching
- Font analysis algorithms
- Heuristic scoring systems

This keeps the solution lightweight (<10MB) and ensures offline operation.

## Building and Running

### Build the Docker Image
```bash
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Run the Container
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:latest
```

## Input/Output Format

**Input:** PDF files in `/app/input/` directory

**Output:** JSON files in `/app/output/` directory with format:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "1.1 Overview",
      "page": 2
    }
  ]
}
```

## Performance Characteristics

- **Speed**: ~2-3 seconds for 50-page documents
- **Memory**: <100MB RAM usage
- **Size**: Container ~150MB
- **Scalability**: Processes multiple PDFs automatically

## Error Handling

- Graceful handling of corrupted PDFs
- Fallback mechanisms for missing formatting
- Outputs valid JSON even on processing errors
- Comprehensive logging for debugging

## Testing Considerations

The solution has been designed to handle:
- Simple academic papers
- Complex technical documents
- Multi-column layouts
- Various font combinations
- Different PDF generators
- Multilingual content

## Architecture

```
PDFOutlineExtractor
├── extract_text_with_formatting() - Extract text with metadata
├── classify_heading_level() - Multi-criteria heading classification
├── extract_title() - Smart title detection
└── extract_outline() - Main processing pipeline
```

The modular design allows easy extension for Round 1B requirements.