import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# Utility helpers
# ----------------------------------------------------

def _clean_pdf_text(text: str) -> str:
    """
    Normalize broken PDF text. This includes:
    - removing stray encoding tokens like (cid:2)
    - fixing mid word newlines
    - collapsing excess whitespace
    """
    if not text:
        return ""

    text = text.replace("(cid:2)", " ")
    text = text.replace("\t", " ")

    # Merge lines that break in the middle of sentences
    text = re.sub(r"(?<![\.\!\?])\n(?=[a-z0-9])", " ", text)

    # Remove repeated blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean leading/trailing whitespace
    return text.strip()


def _strip_line_junk(line: str) -> str:
    """
    Clean a single line of:
    - leading bullets
    - corrupted unicode bullets
    - excess whitespace
    """
    line = line.replace("(cid:2)", "")
    line = re.sub(r"^[\-\*\u2022\u25cf\u25aa\u25e6\•\·\●\□\▪\◦\s]+", "", line)
    line = line.strip()
    return line


def _looks_like_toc(line: str) -> bool:
    """
    Detect table of contents lines, which typically end with dot leaders and page numbers.
    """
    return bool(re.search(r"\.{5,}\s*\d+$", line))


def _is_heading(line: str) -> bool:
    """
    Detect uppercase or title case headings that are not criteria.
    """
    if line.isupper() and len(line.split()) <= 6:
        return True
    if re.match(r"^\d+\.\d+\s+[A-Za-z ]+$", line):
        return True
    return False


def _is_noise(line: str) -> bool:
    """
    Identify lines that are clearly not criteria.
    Examples include:
    - dosing schedules
    - administrative instructions
    - trial duration info
    - visit flow information
    """
    noise_patterns = [
        r"randomi[sz]ation",
        r"visit",
        r"weeks?",
        r"days?",
        r"screening",
        r"treatment period",
        r"dose",
        r"pharmacokinetic",
        r"number of subjects",
        r"maintenance period",
        r"follow-up",
    ]
    return any(re.search(p, line, re.I) for p in noise_patterns)


# ----------------------------------------------------
# Extractor functions
# ----------------------------------------------------

def _extract_block(text: str, start_label: str, end_label: str) -> str:
    """
    Extract the text block between two headings.
    Returns an empty string if bounds cannot be found.
    """
    try:
        start = re.search(start_label, text, flags=re.I)
        end = re.search(end_label, text, flags=re.I)

        if not start:
            return ""

        start_pos = text.find("\n", start.end())
        if start_pos == -1:
            start_pos = start.end()

        if end:
            end_pos = end.start()
            return text[start_pos:end_pos].strip()
        else:
            return text[start_pos:].strip()

    except Exception:
        return ""


def _parse_block(block: str, prefix: str) -> List[dict]:
    """
    Parse a text block into a list of criteria.
    Supports:
    - numbered lists
    - bullet lists
    - sentence splitting fallback
    """
    if not block:
        return []

    lines = [l.strip() for l in block.split("\n") if l.strip()]
    items = []

    bullet_pattern = re.compile(r"^[\-\*\u2022\u25cf\u25aa\u25e6\•\·\●\□\▪\◦]\s+")
    number_pattern = re.compile(r"^(\d+[\.\)]\s*|\([a-z0-9]+\)\s*)", re.I)

    for line in lines:
        if _looks_like_toc(line):
            continue
        if _is_heading(line):
            continue
        if _is_noise(line):
            continue

        if bullet_pattern.match(line) or number_pattern.match(line):
            cleaned = _strip_line_junk(line)
            if len(cleaned) > 5:
                items.append(cleaned)

    # If no valid bullets or numbers found, fallback to sentence splitting
    if not items:
        sentences = re.split(r"(?<=[\.!\?])\s+", block)
        for s in sentences:
            s = s.strip()
            if len(s) > 15 and not _is_noise(s):
                items.append(s)

    out = []
    for i, t in enumerate(items, start=1):
        out.append({"id": f"{prefix}{i}", "text": t.strip(), "type": "text"})

    return out


# ----------------------------------------------------
# Main extractor
# ----------------------------------------------------

def extract_criteria_heuristic(text: str) -> Tuple[List[dict], List[dict]]:
    """
    Heuristic eligibility extractor.
    Returns:
        (inclusion_list, exclusion_list)
    """
    if not text:
        return [], []

    text = _clean_pdf_text(text)

    inc_block = _extract_block(
        text,
        start_label=r"inclusion\s+criteria",
        end_label=r"(exclusion\s+criteria|exclusion\s+criteria\s+for|inclusion\s+and\s+exclusion\s+criteria|exclusion)"
    )
    exc_block = _extract_block(
        text,
        start_label=r"exclusion\s+criteria",
        end_label=r"(lifestyle considerations|study procedures|visit|treatments|trial population)"
    )

    # Fallback: if no clear inclusion/exclusion blocks, look for a broader eligibility section
    if not inc_block and not exc_block:
        elig_block = _extract_block(
            text,
            start_label=r"(eligibility\s+criteria|eligibility)",
            end_label=r"(treatments|trial population|study procedures|visit)"
        )
        if elig_block:
            lines = [l for l in elig_block.split("\n") if l.strip()]
            mid = len(lines) // 2
            if mid > 0:
                inc_block = "\n".join(lines[:mid])
                exc_block = "\n".join(lines[mid:])

    inclusion = _parse_block(inc_block, "INC")
    exclusion = _parse_block(exc_block, "EXC")

    logger.info(f"Heuristic extracted {len(inclusion)} inclusion and {len(exclusion)} exclusion criteria")

    return inclusion, exclusion