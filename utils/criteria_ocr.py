import logging
import os
from typing import Optional, List, TYPE_CHECKING
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)

# Type-checking friendly import for PaddleOCR
if TYPE_CHECKING:
    from paddleocr import PaddleOCR  # pragma: no cover
else:
    PaddleOCR = object  # type: ignore

# Try loading PaddleOCR at runtime
try:
    from paddleocr import PaddleOCR as _RuntimePaddleOCR
    _PADDLE_AVAILABLE = True
except Exception:
    _RuntimePaddleOCR = None  # type: ignore
    _PADDLE_AVAILABLE = False

# Try loading EasyOCR as fallback
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except Exception:
    _EASYOCR_AVAILABLE = False


def _load_paddle_ocr() -> Optional[PaddleOCR]:
    """
    Attempt to initialize PaddleOCR. If it fails, return None.
    """
    if not _PADDLE_AVAILABLE:
        return None

    try:
        # Use English only by default
        ocr = _RuntimePaddleOCR(use_angle_cls=True, lang="en")  # type: ignore
        return ocr
    except Exception as e:
        logger.warning(f"PaddleOCR failed to initialize: {e}")
        return None


def _load_easyocr_reader() -> Optional[object]:
    """
    Attempt to initialize EasyOCR. If it fails, return None.
    """
    if not _EASYOCR_AVAILABLE:
        return None

    try:
        reader = easyocr.Reader(["en"], gpu=False)
        return reader
    except Exception as e:
        logger.warning(f"EasyOCR failed to initialize: {e}")
        return None


def _ocr_page_with_paddle(ocr: PaddleOCR, image: Image.Image) -> str:
    """
    Run OCR on a page image using PaddleOCR.
    """
    try:
        result = ocr.ocr(image, cls=True)
        texts = []
        for block in result:
            for line in block:
                if len(line) >= 2 and line[1]:
                    texts.append(str(line[1][0]))
        return "\n".join(texts)
    except Exception as e:
        logger.warning(f"PaddleOCR failed on a page: {e}")
        return ""


def _ocr_page_with_easyocr(reader, image: Image.Image) -> str:
    """
    Run OCR on a page image using EasyOCR.
    """
    try:
        result = reader.readtext(image)
        texts = []
        for item in result:
            if len(item) >= 2:
                texts.append(str(item[1]))
        return "\n".join(texts)
    except Exception as e:
        logger.warning(f"EasyOCR failed on a page: {e}")
        return ""


def extract_text_via_ocr(pdf_path: str) -> str:
    """
    Extract text from a PDF using OCR.

    Workflow:
    1. Load PaddleOCR if possible.
    2. If PaddleOCR fails or unavailable, try EasyOCR.
    3. Convert each PDF page to an image.
    4. OCR each page and accumulate text.
    5. Always returns text without raising exceptions.

    Returns:
        A single string containing OCR extracted text.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF path does not exist: {pdf_path}")
        return ""

    paddle = _load_paddle_ocr()
    easy_reader = None if paddle else _load_easyocr_reader()

    if not paddle and not easy_reader:
        logger.warning("Neither PaddleOCR nor EasyOCR is available. OCR disabled.")
        return ""

    try:
        pages = convert_from_path(pdf_path)
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return ""

    all_text: List[str] = []

    for idx, page_image in enumerate(pages):
        try:
            img = page_image.convert("RGB")
        except Exception:
            continue

        if paddle:
            ocr_text = _ocr_page_with_paddle(paddle, img)
        else:
            ocr_text = _ocr_page_with_easyocr(easy_reader, img)

        if ocr_text.strip():
            all_text.append(ocr_text)

    final_text = "\n\n".join(all_text)
    return final_text.strip()