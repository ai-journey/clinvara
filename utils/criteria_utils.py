import re
from typing import List, Tuple


def _clean_line(line: str) -> str:
    return re.sub(r'^[\-\*\u2022\d\)\.]+' , '', line).strip()


def _parse_block(block: str, prefix: str) -> List[dict]:
    """Convert a block of text into a list of criteria dicts.

    This is a simple, heuristic parser that looks for bullets or breaks
    and falls back to sentence-splitting if needed.
    """
    if not block or not block.strip():
        return []

    # Split into lines and collect candidates
    lines = [l.strip() for l in re.split(r'\r?\n', block) if l.strip()]
    items = []

    # If there are explicit bullets/numbered lines, keep those
    for l in lines:
        if re.match(r'^[\-\*\u2022\d\)\.]', l):
            items.append(_clean_line(l))

    # If no bullets detected, try splitting paragraphs into sentences
    if not items:
        sents = re.split(r'(?<=[\.\?\!])\s+', block)
        items = [s.strip() for s in sents if len(s.strip()) > 6]

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
    """Attempt to extract inclusion and exclusion criteria from protocol text.

    Returns (inclusion_list, exclusion_list) where each list contains dicts
    with keys `id`, `text`, and `type`.

    This function uses simple heading-based heuristics and will not be as
    accurate as an LLM/NLP model. It's intended to provide a working
    baseline that can be replaced by a model-backed extractor later.
    """
    if not text or not text.strip():
        return [], []

    # Try to find explicit "Inclusion" and "Exclusion" sections
    inc_match = re.search(r'inclusion criteria[:\s\n]*(.*?)(?=(exclusion criteria[:\s\n]|$))', text, re.I | re.S)
    exc_match = re.search(r'exclusion criteria[:\s\n]*(.*?)(?=(inclusion criteria[:\s\n]|$))', text, re.I | re.S)

    inc_block = inc_match.group(1).strip() if inc_match else ""
    exc_block = exc_match.group(1).strip() if exc_match else ""

    # If headings weren't found, try to find a combined 'eligibility' section
    if not inc_block and not exc_block:
        elig_match = re.search(r'eligib(?:ility|le) criteria[:\s\n]*(.*)', text, re.I | re.S)
        if elig_match:
            # naive split by the words 'exclusion' if present
            content = elig_match.group(1)
            parts = re.split(r'(?i)exclusion criteria', content, maxsplit=1)
            inc_block = parts[0].strip()
            if len(parts) > 1:
                exc_block = parts[1].strip()

    inclusion = _parse_block(inc_block, "INC")
    exclusion = _parse_block(exc_block, "EXC")

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
        import openai

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        openai.api_key = api_key

        prompt = (
            "Extract the eligibility criteria from the following clinical trial protocol text. "
            "Return ONLY a JSON object with two keys: \"inclusion\" and \"exclusion\". "
            "Each value should be an array of objects with keys: id (string), text (string). "
            "Number IDs sequentially as INC1, INC2... and EXC1, EXC2... Use concise criterion text.\n\n"
            f"TEXT:\n{text}"
        )

        resp = openai.ChatCompletion.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800,
        )

        content = resp["choices"][0]["message"]["content"].strip()

        # Try to load JSON directly. Some models may add markdown fences — strip them.
        if content.startswith("```"):
            # remove code fence
            content = re.sub(r"^```(?:json)?\s*|```$", "", content).strip()

        parsed = json.loads(content)
        inclusion = parsed.get("inclusion") or parsed.get("inclusions") or []
        exclusion = parsed.get("exclusion") or parsed.get("exclusions") or []

        # Ensure IDs and minimal shape
        def _normalize(items, prefix):
            out = []
            for i, it in enumerate(items, start=1):
                if isinstance(it, dict):
                    tid = it.get("id") or f"{prefix}{i}"
                    txt = it.get("text") or it.get("criterion") or str(it)
                else:
                    tid = f"{prefix}{i}"
                    txt = str(it)
                out.append({"id": tid, "text": txt, "type": "text"})
            return out

        return _normalize(inclusion, "INC"), _normalize(exclusion, "EXC")

    except Exception:
        # If anything fails (missing package/key or parsing error), fallback
        return extract_criteria_from_text(text)
