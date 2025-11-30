import logging
from typing import List, Tuple
from difflib import SequenceMatcher

from .criteria_utils import extract_criteria_heuristic
from .criteria_ocr import extract_text_via_ocr
from .criteria_llm import extract_criteria_via_llm

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# String similarity helper
# ----------------------------------------------------

def _similar(a: str, b: str) -> float:
    """
    Compute a similarity ratio between two strings.
    Used for de-duplication and consensus matching.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ----------------------------------------------------
# Merge and deduplicate
# ----------------------------------------------------

def _merge_lists(heuristic: List[dict], ocr: List[dict], llm: List[dict], prefix: str) -> List[dict]:
    """
    Merge criteria from three sources:
    1. LLM (highest confidence)
    2. OCR (medium)
    3. Heuristic (fallback)

    Deduplicate similar items using a similarity threshold.
    """

    merged: List[dict] = []
    used = []

    sources = [
        ("llm", llm, 3),
        ("ocr", ocr, 2),
        ("heuristic", heuristic, 1),
    ]

    for name, items, weight in sources:
        for item in items:
            text = item["text"].strip()
            if not text:
                continue

            duplicate = False
            for used_item in used:
                if _similar(text, used_item["text"]) >= 0.80:
                    duplicate = True
                    break

            if not duplicate:
                used.append({"text": text, "weight": weight, "source": name})

    # Sort by weight descending (LLM first)
    used.sort(key=lambda x: x["weight"], reverse=True)

    # Reassign cleaned IDs
    final_list = []
    for i, entry in enumerate(used, start=1):
        final_list.append({
            "id": f"{prefix}{i}",
            "text": entry["text"],
            "type": "text",
            "source": entry["source"],
            "weight": entry["weight"]
        })

    return final_list


# ----------------------------------------------------
# Main entry point
# ----------------------------------------------------

def extract_all_criteria(text: str, pdf_path: str) -> Tuple[List[dict], List[dict]]:
    """
    Combined extraction pipeline that runs:
    1. Heuristic extraction on raw PDF text
    2. OCR extraction for corrupted or image based pages
    3. LLM strict JSON extraction
    4. Merges results with scoring, weighting, and de-duplication

    Returns:
        inclusion_list, exclusion_list
    """

    if not text:
        logger.warning("No raw text provided to consensus extractor")
        text = ""

    # 1. Heuristic extraction
    heu_inc, heu_exc = extract_criteria_heuristic(text)
    logger.info(
        f"Heuristic returned {len(heu_inc)} inclusion and {len(heu_exc)} exclusion criteria"
    )

    # 2. OCR extraction (used only if needed)
    ocr_text = extract_text_via_ocr(pdf_path)
    if ocr_text:
        ocr_inc, ocr_exc = extract_criteria_heuristic(ocr_text)
        logger.info(
            f"OCR returned {len(ocr_inc)} inclusion and {len(ocr_exc)} exclusion criteria"
        )
    else:
        ocr_inc, ocr_exc = [], []

    # 3. LLM extraction
    llm_inc, llm_exc = extract_criteria_via_llm(text)
    logger.info(
        f"LLM returned {len(llm_inc)} inclusion and {len(llm_exc)} exclusion criteria"
    )

    # 4. Merge all three lists
    final_inclusion = _merge_lists(heu_inc, ocr_inc, llm_inc, prefix="INC")
    final_exclusion = _merge_lists(heu_exc, ocr_exc, llm_exc, prefix="EXC")

    logger.info(
        f"Consensus extractor produced {len(final_inclusion)} inclusion "
        f"and {len(final_exclusion)} exclusion criteria"
    )

    return final_inclusion, final_exclusion