"""
Document Processor Service
Handles PDF, Word, image OCR, and audio transcription for full text extraction
"""
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import uuid

# Document extraction libraries (graceful import)
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import subprocess
import shutil
import os
import logging

logger = logging.getLogger(__name__)

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import UPLOADS_DIR, TESSERACT_CMD, OCR_LANGUAGE


class DocumentProcessor:
    """
    Document processing pipeline for full text extraction.
    Supports: PDF, DOCX, DOC, TXT, images (OCR), audio (future)
    """

    def __init__(self):
        self.supported_text = ['.txt', '.md', '.csv']
        self.supported_pdf = ['.pdf']
        self.supported_word = ['.docx', '.doc']
        self.supported_image = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        self.supported_audio = ['.mp3', '.wav', '.m4a', '.ogg']

        # Configure Tesseract if available
        if HAS_OCR:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Main entry point for document processing.
        Returns extracted text and metadata.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        file_hash = self.get_file_hash(file_path)

        result = {
            "id": str(uuid.uuid4()),
            "filename": file_path.name,
            "original_path": str(file_path),
            "file_hash": file_hash,
            "processed_at": datetime.now().isoformat(),
            "full_text": "",
            "word_count": 0,
            "page_count": 0,
            "ocr_quality": None,
            "extraction_method": None,
            "errors": []
        }

        try:
            if ext in self.supported_pdf:
                text, pages, ocr_quality = await self._extract_pdf(file_path)
                result["full_text"] = text
                result["page_count"] = pages
                result["ocr_quality"] = ocr_quality
                result["extraction_method"] = "pdf_ocr" if ocr_quality else "pdf_text"

            elif ext in self.supported_word:
                text, pages = await self._extract_word(file_path)
                result["full_text"] = text
                result["page_count"] = pages
                result["extraction_method"] = "docx"

            elif ext in self.supported_text:
                text = await self._extract_text(file_path)
                result["full_text"] = text
                result["extraction_method"] = "plaintext"

            elif ext in self.supported_image:
                text, quality = await self._ocr_image(file_path)
                result["full_text"] = text
                result["page_count"] = 1
                result["ocr_quality"] = quality
                result["extraction_method"] = "ocr"

            elif ext in self.supported_audio:
                text = await self._transcribe_audio(file_path)
                result["full_text"] = text
                result["extraction_method"] = "transcription"

            else:
                result["errors"].append(f"Unsupported file type: {ext}")

            # Calculate word count
            if result["full_text"]:
                result["word_count"] = len(result["full_text"].split())

        except Exception as e:
            result["errors"].append(str(e))

        return result

    async def _extract_pdf(self, file_path: Path) -> Tuple[str, int, Optional[float]]:
        """
        Extract text from PDF with OCR fallback for scanned documents.
        Returns: (text, page_count, ocr_quality or None)
        """
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF (fitz) not installed. Run: pip install PyMuPDF")

        doc = fitz.open(str(file_path))
        text_parts = []
        ocr_used = False
        ocr_qualities = []

        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")

            # Check if page appears to be scanned (very little text)
            if len(page_text.strip()) < 50 and HAS_OCR:
                # Attempt OCR
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img, lang=OCR_LANGUAGE)

                    if len(ocr_text.strip()) > len(page_text.strip()):
                        page_text = ocr_text
                        ocr_used = True
                        # Estimate OCR quality based on confidence data
                        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                        confidences = [int(c) for c in ocr_data['conf'] if c != '-1']
                        if confidences:
                            ocr_qualities.append(sum(confidences) / len(confidences) / 100)

                except Exception as e:
                    text_parts.append(f"[OCR Error on page {page_num + 1}: {str(e)}]")

            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

        doc.close()

        full_text = "\n\n".join(text_parts)
        page_count = len(text_parts)
        avg_ocr_quality = sum(ocr_qualities) / len(ocr_qualities) if ocr_qualities else None

        return full_text, page_count, avg_ocr_quality if ocr_used else None

    async def _extract_word(self, file_path: Path) -> Tuple[str, int]:
        """Extract text from Word documents (.docx)."""
        if not HAS_DOCX:
            raise ImportError("python-docx not installed. Run: pip install python-docx")

        ext = file_path.suffix.lower()

        if ext == '.docx':
            doc = DocxDocument(str(file_path))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = "\n\n".join(paragraphs)

            # Estimate page count (rough: ~500 words per page)
            word_count = len(text.split())
            page_count = max(1, word_count // 500)

            return text, page_count

        elif ext == '.doc':
            # Try to convert .doc to text using LibreOffice or antiword
            text = await self._extract_doc_legacy(file_path)
            word_count = len(text.split())
            page_count = max(1, word_count // 500)
            return text, page_count

    async def _extract_text(self, file_path: Path) -> str:
        """Extract text from plain text files."""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(f"Could not decode text file with any supported encoding")

    async def _ocr_image(self, file_path: Path) -> Tuple[str, float]:
        """Perform OCR on an image file."""
        if not HAS_OCR:
            raise ImportError("pytesseract and Pillow not installed. Run: pip install pytesseract Pillow")

        img = Image.open(str(file_path))

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        text = pytesseract.image_to_string(img, lang=OCR_LANGUAGE)

        # Get confidence scores
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in ocr_data['conf'] if c != '-1']
        quality = sum(confidences) / len(confidences) / 100 if confidences else 0.5

        return text, quality

    async def _extract_doc_legacy(self, file_path: Path) -> str:
        """
        Extract text from legacy .doc files using available tools.
        Tries: antiword, catdoc, LibreOffice (in order of preference).
        """
        # Try antiword first (fastest, most common)
        if shutil.which('antiword'):
            try:
                result = subprocess.run(
                    ['antiword', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    return result.stdout
            except subprocess.TimeoutExpired:
                logger.warning(f"antiword timeout for {file_path.name}")
            except Exception as e:
                logger.warning(f"antiword failed: {e}")

        # Try catdoc
        if shutil.which('catdoc'):
            try:
                result = subprocess.run(
                    ['catdoc', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    return result.stdout
            except subprocess.TimeoutExpired:
                logger.warning(f"catdoc timeout for {file_path.name}")
            except Exception as e:
                logger.warning(f"catdoc failed: {e}")

        # Try LibreOffice conversion
        soffice = shutil.which('soffice') or shutil.which('libreoffice')
        if soffice:
            try:
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    result = subprocess.run(
                        [soffice, '--headless', '--convert-to', 'txt:Text',
                         '--outdir', tmpdir, str(file_path)],
                        capture_output=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        txt_file = Path(tmpdir) / (file_path.stem + '.txt')
                        if txt_file.exists():
                            return txt_file.read_text(encoding='utf-8', errors='ignore')
            except subprocess.TimeoutExpired:
                logger.warning(f"LibreOffice timeout for {file_path.name}")
            except Exception as e:
                logger.warning(f"LibreOffice conversion failed: {e}")

        raise NotImplementedError(
            f".doc file extraction requires antiword, catdoc, or LibreOffice. "
            f"Install one of these tools or convert {file_path.name} to .docx"
        )

    async def _transcribe_audio(self, file_path: Path) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper API.
        Falls back to local whisper if available.
        """
        # Try OpenAI Whisper API first
        if HAS_OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    client = openai.OpenAI(api_key=api_key)
                    with open(file_path, 'rb') as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"
                        )
                    return transcript
                except Exception as e:
                    logger.warning(f"OpenAI Whisper API failed: {e}")

        # Try local whisper command
        if shutil.which('whisper'):
            try:
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    result = subprocess.run(
                        ['whisper', str(file_path), '--output_dir', tmpdir,
                         '--output_format', 'txt', '--language', 'en'],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 min timeout for audio
                    )
                    if result.returncode == 0:
                        txt_file = Path(tmpdir) / (file_path.stem + '.txt')
                        if txt_file.exists():
                            return txt_file.read_text()
            except subprocess.TimeoutExpired:
                logger.warning(f"Local whisper timeout for {file_path.name}")
            except Exception as e:
                logger.warning(f"Local whisper failed: {e}")

        raise NotImplementedError(
            f"Audio transcription requires OpenAI API key (OPENAI_API_KEY env var) "
            f"or local whisper installation. File: {file_path.name}"
        )

    def get_capabilities(self) -> Dict[str, Any]:
        """Return current processing capabilities based on installed libraries."""
        # Check for audio transcription capability
        has_audio = (
            (HAS_OPENAI and os.getenv('OPENAI_API_KEY')) or
            shutil.which('whisper') is not None
        )
        # Check for .doc support
        has_doc = (
            shutil.which('antiword') or
            shutil.which('catdoc') or
            shutil.which('soffice') or
            shutil.which('libreoffice')
        )
        return {
            "pdf": HAS_PYMUPDF,
            "docx": HAS_DOCX,
            "doc": has_doc is not None,
            "ocr": HAS_OCR,
            "audio": has_audio,
            "supported_extensions": (
                self.supported_text +
                (self.supported_pdf if HAS_PYMUPDF else []) +
                (['.docx'] if HAS_DOCX else []) +
                (['.doc'] if has_doc else []) +
                (self.supported_image if HAS_OCR else []) +
                (self.supported_audio if has_audio else [])
            )
        }


# Singleton instance
_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get or create document processor instance."""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor
