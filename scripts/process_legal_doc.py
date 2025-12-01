"""Process the legal document PDF with OCR."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.document_processor import DocumentProcessor
from pathlib import Path
import asyncio

async def process():
    processor = DocumentProcessor()
    caps = processor.get_capabilities()
    print('Processing capabilities:')
    print(f'  PDF: {caps["pdf"]}')
    print(f'  OCR: {caps["ocr"]}')
    
    pdf_path = Path('Document_2025-11-30_225038.pdf')
    if not pdf_path.exists():
        print(f'File not found: {pdf_path}')
        return
    
    if caps['pdf']:
        print(f'\nProcessing {pdf_path}...')
        result = await processor.process_document(pdf_path)
        print(f'Pages: {result["page_count"]}')
        print(f'Words: {result["word_count"]}')
        print(f'OCR Quality: {result.get("ocr_quality", "N/A")}')
        print(f'Method: {result.get("extraction_method", "unknown")}')
        
        if result.get('errors'):
            print(f'Errors: {result["errors"]}')
        
        print()
        print('=' * 60)
        print('EXTRACTED TEXT (first 3000 chars):')
        print('=' * 60)
        print(result['full_text'][:3000])
        
        # Save the extracted text
        os.makedirs('data', exist_ok=True)
        with open('data/extracted_doc_2025-11-30.txt', 'w', encoding='utf-8') as f:
            f.write(result['full_text'])
        print('\n' + '=' * 60)
        print(f'Full text saved to data/extracted_doc_2025-11-30.txt')
        print(f'Total characters: {len(result["full_text"])}')
    else:
        print('PDF processing not available - install PyMuPDF')

if __name__ == '__main__':
    asyncio.run(process())

