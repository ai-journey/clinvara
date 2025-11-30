import logging
import json
from typing import List, Tuple

from openai import OpenAI
from openai.types.responses import ResponseOutput

logger = logging.getLogger(__name__)

client = OpenAI()


def _build_schema():
    """
    Builds a strict JSON schema for the OpenAI parser
    that enforces the structure of the extracted criteria.
    """
    return {
        "type": "object",
        "properties": {
            "inclusion": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["id", "text"]
                }
            },
            "exclusion": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["id", "text"]
                }
            }
        },
        "required": ["inclusion", "exclusion"]
    }


def _normalize_items(items: List[dict], prefix: str) -> List[dict]:
    """
    Normalize LLM extracted items:
    - Guarantees IDs are present
    - Strips whitespace
    - Sets type as text
    """
    normalized = []
    for i, item in enumerate(items, start=1):
        text = str(item.get("text", "")).strip()
        cid = item.get("id") or f"{prefix}{i}"
        normalized.append({"id": cid, "text": text, "type": "text"})
    return normalized


def extract_criteria_via_llm(text: str) -> Tuple[List[dict], List[dict]]:
    """
    Uses OpenAI responses.parse to extract inclusion and exclusion criteria
    with strict schema validation. The model will only return JSON that matches
    the schema, with no extra text allowed.

    Returns:
        inclusion_list, exclusion_list
    """
    if not text or not text.strip():
        logger.warning("LLM extraction received empty text")
        return [], []

    schema = _build_schema()
    prompt = (
        "You are an expert clinical trial protocol analyst. Extract all inclusion "
        "and all exclusion criteria from the provided protocol text. Do not add "
        "information that is not explicitly present. Keep each criterion complete "
        "but concise. Return only data that matches the schema.\n\n"
        "Protocol text begins here:\n"
        f"{text}\n"
        "Protocol text ends here."
    )

    try:
        result: ResponseOutput = client.responses.parse(
            model="gpt-4.1-mini",
            input=prompt,
            response_format=schema
        )

        data = result.output_parsed
        inclusion = data.get("inclusion", [])
        exclusion = data.get("exclusion", [])

        inc_norm = _normalize_items(inclusion, "INC")
        exc_norm = _normalize_items(exclusion, "EXC")

        logger.info(
            f"LLM extracted {len(inc_norm)} inclusion and {len(exc_norm)} exclusion criteria"
        )

        return inc_norm, exc_norm

    except Exception as e:
        logger.error(f"LLM strict parser failed: {e}")
        return [], []