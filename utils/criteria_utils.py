import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def _clean_line(line: str) -> str:
    """Remove leading bullets, numbers, dashes, etc."""
    return re.sub(r'^[\-\*\u2022\d\)\.\s]+', '', line).strip()


def _parse_block(block: str, prefix: str) -> List[dict]:
    """Convert a block of text into a list of criteria dicts.

    This parser looks for bullets, numbered lines, or falls back to
    sentence-splitting.
    """
    if not block or not block.strip():
        return []

    # Normalize whitespace
    block = re.sub(r'\r\n?', '\n', block)

    # Split into lines
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    items = []

    # Patterns for bulleted or numbered lines
    bullet_pattern = re.compile(r'^[\-\*\u2022\u25cf\u25aa\u25e6]\s*')
    number_pattern = re.compile(r'^(\d+[\.\)\:]\s*|\([a-z0-9]+\)\s*|[a-z][\.\)]\s*)', re.I)

    for l in lines:
        # Check for bullet or number prefix first
        is_bullet = bullet_pattern.match(l)
        is_number = number_pattern.match(l)
        
        if is_bullet or is_number:
            # Remove the bullet/number prefix
            if is_bullet:
                cleaned = bullet_pattern.sub('', l).strip()
            else:
                cleaned = number_pattern.sub('', l).strip()
            
            # Skip if too short or looks like a sub-heading
            if cleaned and len(cleaned) > 5:
                # Skip lines that are just headings
                if cleaned.lower() in ['inclusion criteria', 'exclusion criteria', 'eligibility criteria']:
                    continue
                items.append(cleaned)
        else:
            # Non-bulleted line - could be continuation or intro text
            # Skip short lines and heading-like lines
            if len(l) < 15:
                continue
            if l.isupper() and len(l.split()) < 6:
                continue
            # Skip intro phrases
            if re.match(r'^(patients?\s+(must|should|meeting|who)|the\s+following|subjects?\s+(must|should|meeting|who))', l, re.I):
                continue

    # Fallback: if no bullets/numbers found, try sentence splitting
    if not items:
        # Join lines to form paragraph and split by sentence-ending punctuation
        para = ' '.join(lines)
        sents = re.split(r'(?<=[\.!\?])\s+', para)
        items = [s.strip() for s in sents if len(s.strip()) > 15]

    # Build structured output
    out = []
    for i, t in enumerate(items, start=1):
        out.append({
            "id": f"{prefix}{i}",
            "text": t,
            "type": "text",
        })
    return out


def extract_criteria_from_text(text: str) -> Tuple[List[dict], List[dict]]:
    """Extract inclusion and exclusion criteria from protocol text using heuristics.

    Returns (inclusion_list, exclusion_list) where each list contains dicts
    with keys `id`, `text`, and `type`.
    """
    if not text or not text.strip():
        logger.warning("extract_criteria_from_text received empty text")
        return [], []

    # Normalize line endings and collapse multiple blank lines
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    inc_block = ""
    exc_block = ""

    # Find positions of inclusion and exclusion headings using simple patterns
    inc_heading = re.search(r'inclusion\s+criteria', text, re.I)
    exc_heading = re.search(r'exclusion\s+criteria', text, re.I)

    def find_line_start(text: str, pos: int) -> int:
        """Find the start of the line containing position pos."""
        line_start = text.rfind('\n', 0, pos)
        return line_start + 1 if line_start != -1 else 0

    def find_line_end(text: str, pos: int) -> int:
        """Find the end of the line containing position pos."""
        line_end = text.find('\n', pos)
        return line_end if line_end != -1 else len(text)

    if inc_heading and exc_heading:
        # Get line boundaries for both headings
        inc_line_start = find_line_start(text, inc_heading.start())
        inc_line_end = find_line_end(text, inc_heading.end())
        exc_line_start = find_line_start(text, exc_heading.start())
        exc_line_end = find_line_end(text, exc_heading.end())
        
        if inc_heading.start() < exc_heading.start():
            # Inclusion comes before exclusion
            inc_block = text[inc_line_end:exc_line_start].strip()
            exc_block = text[exc_line_end:].strip()
        else:
            # Exclusion comes before inclusion
            exc_block = text[exc_line_end:inc_line_start].strip()
            inc_block = text[inc_line_end:].strip()
            
        # Trim blocks at next major section heading (but not numbered criteria items)
        # Match patterns like "5. Study Procedures" or "STUDY PROCEDURES" but not "1. Age >= 18"
        section_patterns = [
            r'\n\s*\d+[\.\)]\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # "5. Study Procedures" (two+ capitalized words)
            r'\n\s*[A-Z][A-Z\s]{8,}\n',                     # All caps headings with 8+ chars
        ]
        for pattern in section_patterns:
            m = re.search(pattern, inc_block)
            if m:
                inc_block = inc_block[:m.start()].strip()
            m = re.search(pattern, exc_block)
            if m:
                exc_block = exc_block[:m.start()].strip()
                            
    elif inc_heading:
        # Only inclusion found
        inc_line_end = find_line_end(text, inc_heading.end())
        inc_block = text[inc_line_end:].strip()
    elif exc_heading:
        # Only exclusion found
        exc_line_end = find_line_end(text, exc_heading.end())
        exc_block = text[exc_line_end:].strip()
    else:
        # Try eligibility criteria as a combined section
        elig_match = re.search(r'eligib(?:ility|le)\s+criteria', text, re.I)
        if elig_match:
            elig_line_end = find_line_end(text, elig_match.end())
            content = text[elig_line_end:].strip()
            # Split by exclusion if present within
            exc_split = re.search(r'exclusion', content, re.I)
            if exc_split:
                exc_line_start = find_line_start(content, exc_split.start())
                inc_block = content[:exc_line_start].strip()
                exc_block = content[exc_line_start:].strip()
            else:
                inc_block = content

    logger.debug(f"inc_block length: {len(inc_block)}, exc_block length: {len(exc_block)}")

    # Parse the blocks
    inclusion = _parse_block(inc_block, "INC")
    exclusion = _parse_block(exc_block, "EXC")

    # If still empty, try a last-ditch fallback
    if not inclusion and not exclusion:
        logger.warning("No inclusion/exclusion headings found; attempting fallback extraction")
        fallback_match = re.search(
            r'((?:^|\n)\s*(?:\d+[\.\)]|[\-\*\u2022]).*(?:age|patient|subject|diagnos|disease|treatment|pregnan|exclude|include|eligible|history|years?).*(?:\n\s*(?:\d+[\.\)]|[\-\*\u2022]).*){2,})',
            text, re.I | re.S
        )
        if fallback_match:
            fallback_text = fallback_match.group(1)
            lines = [l.strip() for l in fallback_text.split('\n') if l.strip()]
            mid = len(lines) // 2
            inc_block = '\n'.join(lines[:mid]) if mid > 0 else '\n'.join(lines)
            exc_block = '\n'.join(lines[mid:]) if mid > 0 else ''
            inclusion = _parse_block(inc_block, "INC")
            exclusion = _parse_block(exc_block, "EXC")

    logger.info(f"Extracted {len(inclusion)} inclusion and {len(exclusion)} exclusion criteria (heuristic)")
    return inclusion, exclusion


def extract_criteria(text: str, use_llm: bool = False, llm_model: str = "gpt-4o-mini") -> Tuple[List[dict], List[dict]]:
    """Higher-level extractor that optionally calls an LLM.

    If `use_llm` is True and the `openai` package and `OPENAI_API_KEY`
    are available, this will call the model and expect a JSON response
    with `inclusion` and `exclusion` arrays. On any failure it falls
    back to the heuristic extractor.
    """
    if not use_llm:
        return extract_criteria_from_text(text)

    # Lazy import so this module doesn't require openai for the heuristic path
    try:
        import os
        import json
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; falling back to heuristic extractor")
            raise RuntimeError("OPENAI_API_KEY not set")

        client = OpenAI(api_key=api_key)

        # Truncate text if very long to stay within token limits
        max_chars = 12000
        truncated = text[:max_chars] if len(text) > max_chars else text

        prompt = f"""You are a clinical trial protocol analyst. Extract ALL inclusion criteria and ALL exclusion criteria from the following protocol text.

IMPORTANT INSTRUCTIONS:
1. Return ONLY valid JSON with exactly two keys: "inclusion" and "exclusion"
2. Each key should have an array of objects with "id" and "text" fields
3. Number IDs as INC1, INC2, INC3... for inclusion and EXC1, EXC2, EXC3... for exclusion
4. Extract EVERY criterion mentioned, even if implicit
5. Keep criterion text concise but complete
6. If you cannot find explicit criteria sections, look for eligibility requirements anywhere in the text

Example output format:
{{"inclusion": [{{"id": "INC1", "text": "Age 18 years or older"}}, {{"id": "INC2", "text": "Confirmed diagnosis of condition X"}}], "exclusion": [{{"id": "EXC1", "text": "Pregnant or breastfeeding"}}, {{"id": "EXC2", "text": "Prior treatment with drug Y"}}]}}

PROTOCOL TEXT:
{truncated}

Return ONLY the JSON object, no other text:"""

        resp = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=2000,
        )

        content = resp.choices[0].message.content.strip()
        logger.debug(f"LLM response: {content[:500]}...")

        # Strip markdown code fences if present
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()

        # Try to extract JSON object if there's extra text
        json_match = re.search(r'\{.*\}', content, re.S)
        if json_match:
            content = json_match.group(0)

        parsed = json.loads(content)
        inclusion = parsed.get("inclusion") or parsed.get("inclusions") or []
        exclusion = parsed.get("exclusion") or parsed.get("exclusions") or []

        # Ensure IDs and minimal shape
        def _normalize(items, prefix):
            out = []
            for i, it in enumerate(items, start=1):
                if isinstance(it, dict):
                    tid = it.get("id") or f"{prefix}{i}"
                    txt = it.get("text") or it.get("criterion") or it.get("description") or str(it)
                else:
                    tid = f"{prefix}{i}"
                    txt = str(it)
                out.append({"id": tid, "text": txt, "type": "text"})
            return out

        inc_result = _normalize(inclusion, "INC")
        exc_result = _normalize(exclusion, "EXC")
        logger.info(f"Extracted {len(inc_result)} inclusion and {len(exc_result)} exclusion criteria (LLM)")
        return inc_result, exc_result

    except Exception as e:
        # If anything fails (missing package/key or parsing error), fallback
        logger.warning(f"LLM extraction failed ({e}); falling back to heuristic extractor")
        return extract_criteria_from_text(text)
